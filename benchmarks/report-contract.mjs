import assert from 'node:assert/strict';

const GOAL_CONFIDENCE = new Set(['confirmed', 'inferred', 'unknown']);
const GOAL_STATUSES = new Set(['met', 'advanced', 'blocked', 'replanned', 'not_started']);
const COMMITMENT_STATES = new Set(['confirmed', 'proposed']);
const GOAL_SOURCE_CONFIDENCE = new Map([
  ['current_request', 'confirmed'],
  ['previous_weekly', 'confirmed'],
  ['goal_artifact', 'confirmed'],
  ['raw_inference', 'inferred'],
  ['unknown', 'unknown'],
]);
const MANAGEMENT_FIELDS = new Set([
  'goal_state',
  'actual_change',
  'material_variance',
  'decision_or_support',
  'next_commitment',
  'confidence_boundary',
]);

function present(value) {
  return typeof value === 'string' ? Boolean(value.trim()) : value !== null && value !== undefined;
}

function nonEmptyString(value) {
  return typeof value === 'string' && Boolean(value.trim());
}

function nonEmptyStringArray(value) {
  return Array.isArray(value) && value.length > 0 && value.every(nonEmptyString);
}

function normalizeNarrativeText(value) {
  return String(value || '')
    .toLowerCase()
    .replace(/[^\p{L}\p{N}]+/gu, ' ')
    .trim()
    .replace(/\s+/g, ' ');
}

function normalizeSemanticValue(value) {
  if (typeof value === 'string') {
    return value.replace(/\r\n?/g, '\n').trim().replace(/\s+/g, ' ');
  }
  if (Array.isArray(value)) return value.map(normalizeSemanticValue);
  if (value && typeof value === 'object') {
    return Object.fromEntries(
      Object.entries(value).map(([key, item]) => [key, normalizeSemanticValue(item)]),
    );
  }
  return value;
}

function validateExpectedFraming(fixture, audience, expected) {
  for (const [field, value] of Object.entries(expected || {})) {
    if (value === null) {
      assert(!present(audience[field]), `${fixture.id}: default framing invented ${field}`);
    } else {
      assert.equal(audience[field], value, `${fixture.id}: default framing ${field} is wrong`);
    }
  }
}

function containsForbiddenMainDeckReference(value) {
  const text = String(value || '');
  return /[\u0000-\u001f\u007f-\u009f]/.test(text)
    || /!?\[[^\]]*\]\([^)]*\)/.test(text)
    || /<\/?[A-Za-z][^>]*>/.test(text)
    || /https?:\/\//i.test(text)
    || /(^|[\s(])\/\/[A-Za-z0-9.-]+(?:\/|$)/.test(text)
    || /\bfile:/i.test(text)
    || /%(?:2f|5c)/i.test(text)
    || /\b[A-Za-z]:[\\/][^\s]+/.test(text)
    || /(^|\s)\/(?:[^/\s]+\/)+[^/\s]+/.test(text)
    || /(?:[\w.-]+[\\/]){2,}[\w.-]+(?::\d+)?/.test(text)
    || /\b(?=[0-9a-f]{7,40}\b)(?=[0-9a-f]*[a-f])(?=[0-9a-f]*\d)[0-9a-f]{7,40}\b/i.test(text)
    || /\b[OWDE]\d+\b/.test(text);
}

export function validateReportContract(fixture) {
  const config = fixture.fixture || {};
  const output = config.candidate_output || {};
  if (present(output.format)) {
    assert(['brief', 'slides'].includes(output.format), `${fixture.id}: invalid report format`);
  }
  const groups = Array.isArray(output.groups) ? output.groups : [];
  assert(groups.length > 0, `${fixture.id}: no reporting groups`);

  const seenGroups = new Set();
  for (const group of groups) {
    assert(typeof group.name === 'string' && group.name, `${fixture.id}: missing group name`);
    assert(!seenGroups.has(group.name), `${fixture.id}: duplicate group ${group.name}`);
    seenGroups.add(group.name);
    assert(typeof group.judgment === 'string' && group.judgment.trim(), `${fixture.id}: missing group judgment`);

    const headlines = Array.isArray(group.headlines) ? group.headlines : [];
    assert(headlines.length >= 1, `${fixture.id}: report has no material changes`);
    const portfolio = Array.isArray(group.portfolio) ? group.portfolio : [];
    const covered = new Set([...headlines, ...portfolio]);
    for (const stream of group.all_streams || []) {
      assert(covered.has(stream), `${fixture.id}: uncovered stream ${stream}`);
    }

    const targets = Array.isArray(group.next_closure_targets) ? group.next_closure_targets : [];
    if (output.format === 'slides') {
      for (const target of targets) {
        assert(target && typeof target === 'object' && !Array.isArray(target), `${fixture.id}: slide closure target must be structured`);
        assert(nonEmptyString(target.target), `${fixture.id}: slide closure target name is missing`);
        assert(nonEmptyString(target.closure_criterion), `${fixture.id}: slide closure target criterion is missing`);
      }
    }
  }

  if (output.scope === 'work') {
    assert.deepEqual([...seenGroups], ['work'], `${fixture.id}: work scope must contain only work group`);
    const serialized = JSON.stringify(output).toLowerCase();
    for (const forbidden of config.forbidden_terms || []) {
      assert(!serialized.includes(String(forbidden).toLowerCase()), `${fixture.id}: work output leaked ${forbidden}`);
    }
  }

  if (output.scope === 'all') {
    assert(groups.length >= 2, `${fixture.id}: all scope must preserve separate groups`);
  }
}

function validateGoalLoopOutput(fixture, output) {
  const groups = Array.isArray(output.groups) ? output.groups : [];
  assert(groups.length > 0, `${fixture.id}: no reporting groups`);

  for (const group of groups) {
    assert(nonEmptyString(group.name), `${fixture.id}: missing group name`);
    const goals = Array.isArray(group.goals) ? group.goals : [];
    assert(goals.length > 0, `${fixture.id}: ${group.name} has no goal lane`);
    const goalIds = new Set();
    for (const goal of goals) {
      assert(nonEmptyString(goal.id), `${fixture.id}: goal id is missing`);
      assert(!goalIds.has(goal.id), `${fixture.id}: duplicate goal ${goal.id}`);
      goalIds.add(goal.id);
      assert(nonEmptyString(goal.statement), `${fixture.id}: ${goal.id} statement is missing`);
      assert(GOAL_CONFIDENCE.has(goal.confidence), `${fixture.id}: ${goal.id} confidence is invalid`);
      assert(GOAL_STATUSES.has(goal.status), `${fixture.id}: ${goal.id} status is invalid`);
      assert(COMMITMENT_STATES.has(goal.commitment_state), `${fixture.id}: ${goal.id} commitment state is invalid`);
      assert(nonEmptyString(goal.closure_criterion), `${fixture.id}: ${goal.id} closure criterion is missing`);
      const sourceKind = goal.source?.kind;
      assert(GOAL_SOURCE_CONFIDENCE.has(sourceKind), `${fixture.id}: ${goal.id} source is invalid`);
      const expectedConfidence = sourceKind === 'previous_weekly' && goal.commitment_state === 'proposed'
        ? 'inferred'
        : GOAL_SOURCE_CONFIDENCE.get(sourceKind);
      assert(
        goal.confidence === expectedConfidence,
        `${fixture.id}: ${goal.id} confidence contradicts its source`,
      );
    }

    const priorCommitments = Array.isArray(group.prior_commitments) ? group.prior_commitments : [];
    for (const item of priorCommitments) {
      assert(nonEmptyString(item.statement), `${fixture.id}: prior commitment statement is missing`);
      assert(COMMITMENT_STATES.has(item.commitment_state), `${fixture.id}: prior commitment state is invalid`);
      assert(GOAL_STATUSES.has(item.status), `${fixture.id}: prior commitment status is invalid`);
      assert(goalIds.has(item.goal_id), `${fixture.id}: prior commitment references unknown goal ${item.goal_id}`);
      assert(nonEmptyString(item.reason), `${fixture.id}: prior commitment reason is missing`);
    }

    const changes = Array.isArray(group.material_changes) ? group.material_changes : [];
    const changeIds = new Set();
    for (const change of changes) {
      assert(nonEmptyString(change.id), `${fixture.id}: material change id is missing`);
      assert(!changeIds.has(change.id), `${fixture.id}: duplicate material change ${change.id}`);
      changeIds.add(change.id);
      const linkedGoals = Array.isArray(change.goal_ids) ? change.goal_ids : [];
      assert(
        linkedGoals.length > 0 || change.variance?.kind === 'unplanned',
        `${fixture.id}: ${change.id} is neither goal-linked nor explicitly unplanned`,
      );
      for (const goalId of linkedGoals) {
        assert(goalIds.has(goalId), `${fixture.id}: ${change.id} references unknown goal ${goalId}`);
      }
      if (change.variance?.kind === 'replanned') {
        for (const field of ['prior_direction', 'trigger', 'reason', 'new_direction']) {
          assert(nonEmptyString(change.variance[field]), `${fixture.id}: ${change.id} replan ${field} is missing`);
        }
      }
    }

    const portfolio = new Set(Array.isArray(group.portfolio) ? group.portfolio : []);
    for (const changeId of group.all_changes || []) {
      assert(changeIds.has(changeId) || portfolio.has(changeId), `${fixture.id}: uncovered change ${changeId}`);
    }

    const nextCommitments = Array.isArray(group.next_commitments) ? group.next_commitments : [];
    for (const item of nextCommitments) {
      assert(nonEmptyString(item.statement), `${fixture.id}: next commitment statement is missing`);
      assert(COMMITMENT_STATES.has(item.commitment_state), `${fixture.id}: next commitment state is invalid`);
      assert(nonEmptyString(item.closure_criterion), `${fixture.id}: next commitment criterion is missing`);
    }

    if (fixture.fixture?.expected_min_goal_lanes) {
      assert(
        goals.length >= fixture.fixture.expected_min_goal_lanes,
        `${fixture.id}: unrelated projects were forced into one goal lane`,
      );
    }

    const narrative = String(group.narrative || '');
    if (goals.some((goal) => goal.confidence !== 'confirmed')) {
      assert(!/(原定目标|本周承诺|confirmed goal)/i.test(narrative), `${fixture.id}: uncertain goal uses confirmed language`);
    }
  }

  if (output.scope === 'work') {
    assert.deepEqual(groups.map((group) => group.name), ['work'], `${fixture.id}: work scope must contain only work`);
    const serialized = JSON.stringify(output).toLowerCase();
    for (const forbidden of fixture.fixture?.forbidden_terms || []) {
      assert(!serialized.includes(String(forbidden).toLowerCase()), `${fixture.id}: work output leaked ${forbidden}`);
    }
  }
}

export function validateWeeklyGoalLoopContract(fixture) {
  const outputs = fixture.fixture?.candidate_outputs
    || [fixture.fixture?.candidate_output];
  assert(outputs.every(Boolean), `${fixture.id}: goal-loop candidate output is missing`);
  for (const output of outputs) validateGoalLoopOutput(fixture, output);

  if (fixture.fixture?.expected_distinct_rankings) {
    const rankings = outputs.map((output) => output.groups[0].material_changes.map((change) => change.id).join('|'));
    assert(new Set(rankings).size === rankings.length, `${fixture.id}: different goals produced the same change ranking`);
  }

  if (fixture.fixture?.expected_distinct_narratives) {
    const narratives = outputs.map((output) => normalizeNarrativeText(output.groups[0].narrative));
    assert(new Set(narratives).size === narratives.length, `${fixture.id}: different goals produced the same management meaning`);
  }

  for (const [changeId, closureType] of Object.entries(fixture.fixture?.expected_change_closure_types || {})) {
    const changes = outputs.flatMap((output) => output.groups.flatMap((group) => group.material_changes || []));
    assert(
      changes.some((change) => change.id === changeId && change.closure_type === closureType),
      `${fixture.id}: ${changeId} did not preserve closure type ${closureType}`,
    );
  }

  for (const expected of fixture.fixture?.expected_prior_statements || []) {
    const accounted = outputs[0].groups.flatMap((group) => group.prior_commitments || []);
    assert(accounted.some((item) => item.statement === expected), `${fixture.id}: prior commitment disappeared: ${expected}`);
  }
}

function validateBriefCompressionOutput(fixture, output) {
  assert(nonEmptyString(output.name), `${fixture.id}: compression output name is missing`);
  const model = output.management_model || {};
  for (const field of MANAGEMENT_FIELDS) {
    assert(nonEmptyString(model[field]), `${fixture.id}:${output.name}: management model ${field} is missing`);
  }

  const requiredDeltaIds = new Set(model.required_delta_ids || []);
  assert(requiredDeltaIds.size > 0, `${fixture.id}:${output.name}: required management deltas are missing`);
  const bodyBlocks = Array.isArray(output.body_blocks) ? output.body_blocks : [];
  assert(bodyBlocks.length > 0, `${fixture.id}:${output.name}: brief body is empty`);
  const coveredFields = new Set();
  const deltaCounts = new Map();
  const bodyItemRefs = new Set();
  const blockIds = new Set();
  for (const block of bodyBlocks) {
    assert(nonEmptyString(block.id), `${fixture.id}:${output.name}: body block id is missing`);
    assert(!blockIds.has(block.id), `${fixture.id}:${output.name}: duplicate body block ${block.id}`);
    blockIds.add(block.id);
    assert(nonEmptyString(block.text), `${fixture.id}:${output.name}:${block.id}: body text is missing`);
    assert(!/(^|\n)\s*\|.+\|\s*(\n|$)/.test(block.text), `${fixture.id}:${output.name}:${block.id}: body contains a table`);
    assert(!containsForbiddenMainDeckReference(block.text), `${fixture.id}:${output.name}:${block.id}: body leaks provenance`);
    const covers = Array.isArray(block.covers) ? block.covers : [];
    assert(covers.length > 0, `${fixture.id}:${output.name}:${block.id}: body block changes no management field`);
    for (const field of covers) {
      assert(MANAGEMENT_FIELDS.has(field), `${fixture.id}:${output.name}:${block.id}: invalid management field ${field}`);
      coveredFields.add(field);
    }
    const deltaIds = Array.isArray(block.delta_ids) ? block.delta_ids : [];
    assert(deltaIds.length > 0, `${fixture.id}:${output.name}:${block.id}: body block has no decision delta`);
    for (const deltaId of deltaIds) {
      assert(requiredDeltaIds.has(deltaId), `${fixture.id}:${output.name}:${block.id}: non-required delta ${deltaId} entered the body`);
      deltaCounts.set(deltaId, (deltaCounts.get(deltaId) || 0) + 1);
    }
    for (const itemRef of block.item_refs || []) bodyItemRefs.add(itemRef);
  }
  assert.deepEqual(coveredFields, MANAGEMENT_FIELDS, `${fixture.id}:${output.name}: body cannot reconstruct the management model`);
  for (const deltaId of requiredDeltaIds) {
    assert(deltaCounts.get(deltaId) === 1, `${fixture.id}:${output.name}: decision delta ${deltaId} is missing or repeated`);
  }
  for (const block of bodyBlocks) {
    assert(
      block.delta_ids.some((deltaId) => deltaCounts.get(deltaId) === 1),
      `${fixture.id}:${output.name}:${block.id}: block fails the counterfactual deletion test`,
    );
  }
  for (const itemId of output.body_required_item_ids || []) {
    assert(bodyItemRefs.has(itemId), `${fixture.id}:${output.name}: material item ${itemId} exists only in the appendix`);
  }

  const appendix = output.appendix || {};
  const priorItems = new Set(appendix.prior_item_ids || []);
  for (const itemId of output.all_prior_item_ids || []) {
    assert(priorItems.has(itemId), `${fixture.id}:${output.name}: prior item ${itemId} is missing from the appendix`);
  }
  const workStreams = new Set(appendix.work_stream_ids || []);
  for (const streamId of output.all_work_stream_ids || []) {
    assert(workStreams.has(streamId), `${fixture.id}:${output.name}: work stream ${streamId} is missing from the appendix`);
  }

  const claimEvidence = Array.isArray(appendix.claim_evidence) ? appendix.claim_evidence : [];
  const evidenceByClaim = new Map(claimEvidence.map((claim) => [claim.claim_id, claim]));
  for (const block of bodyBlocks) {
    const claim = evidenceByClaim.get(block.id);
    assert(claim, `${fixture.id}:${output.name}:${block.id}: body claim has no appendix evidence mapping`);
    assert(nonEmptyString(claim.label), `${fixture.id}:${output.name}:${block.id}: evidence label is missing`);
    assert(nonEmptyStringArray(claim.evidence_refs), `${fixture.id}:${output.name}:${block.id}: evidence refs are missing`);
    assert(
      normalizeNarrativeText(claim.label) !== normalizeNarrativeText(block.text),
      `${fixture.id}:${output.name}:${block.id}: appendix repeats the body narrative`,
    );
  }
}

function compressionBodyFingerprint(output) {
  return output.body_blocks.map((block) => `${block.id}:${normalizeNarrativeText(block.text)}`).join('|');
}

function appendixSignalCount(output) {
  const appendix = output.appendix || {};
  return (appendix.prior_item_ids || []).length
    + (appendix.work_stream_ids || []).length
    + (appendix.claim_evidence || []).reduce((total, claim) => total + (claim.evidence_refs || []).length, 0);
}

function validateChangeExplanationCard(fixture, card) {
  const label = `${fixture.id}:${card.id || 'change-card'}`;
  const availableRefs = new Set(fixture.fixture?.change_card_available_source_refs || []);
  assert(nonEmptyString(card.id), `${label}: id is missing`);
  assert(['judgment', 'action', 'confidence'].includes(card.deletion_effect), `${label}: card fails the deletion gate`);
  assert(nonEmptyString(card.comparison_axis), `${label}: comparison axis is missing`);
  assert.equal(card.before_axis, card.comparison_axis, `${label}: Before comparison axis drifted`);
  assert.equal(card.after_axis, card.comparison_axis, `${label}: After comparison axis drifted`);
  for (const field of ['starting_constraint', 'decisive_move', 'end_state', 'management_meaning']) {
    assert(nonEmptyString(card[field]), `${label}: existing result field ${field} is missing`);
  }

  const transition = card.state_transition || {};
  for (const field of ['before', 'intervention', 'after', 'remaining_gate']) {
    assert(nonEmptyString(transition[field]), `${label}: state transition ${field} is missing`);
  }
  assert(nonEmptyStringArray(transition.evidence_refs), `${label}: state transition evidence is missing`);
  for (const ref of transition.evidence_refs) {
    assert(availableRefs.has(ref), `${label}: state transition evidence ${ref} is not available`);
  }
  assert.equal(card.after_status, 'actual', `${label}: After must be the current actual state`);

  assert(nonEmptyStringArray(card.problem_evidence_refs), `${label}: problem or root cause is unsupported`);
  for (const ref of card.problem_evidence_refs) {
    assert(transition.evidence_refs.includes(ref), `${label}: problem evidence is outside the card evidence boundary`);
    assert(availableRefs.has(ref), `${label}: problem evidence ${ref} is not available`);
  }

  const visual = card.visual || {};
  const allowed = ['markdown_table', 'diff', 'mermaid', 'text_trace', 'text_only'];
  assert(allowed.includes(visual.representation), `${label}: visual representation is invalid`);
  assert([0, 1].includes(visual.primary_count), `${label}: card has more than one primary visual`);
  assert.equal(visual.primary_count, visual.representation === 'text_only' ? 0 : 1, `${label}: visual count does not match representation`);
  if (card.simple_result) {
    assert.equal(visual.representation, 'text_only', `${label}: simple result received a decorative visual`);
  }
}

function validateChangeExplanationCardProbes(fixture, cards) {
  for (const probe of fixture.fixture?.change_card_rejection_probes || []) {
    const mutants = structuredClone(cards);
    const card = mutants[0];
    if (probe === 'target-as-after') {
      card.after_status = 'target';
      card.state_transition.after = 'Target design, not yet implemented';
    } else if (probe === 'unsupported-problem') {
      card.problem_evidence_refs = [];
    } else if (probe === 'axis-drift') {
      card.after_axis = 'a different object and measure';
    } else if (probe === 'decorative-simple-result') {
      card.simple_result = true;
      card.visual = {representation: 'mermaid', primary_count: 1};
    } else {
      throw new Error(`${fixture.id}: unknown change card rejection probe ${probe}`);
    }
    assert.throws(
      () => mutants.forEach(item => validateChangeExplanationCard(fixture, item)),
      `${fixture.id}: change card rejection probe ${probe} unexpectedly passed`,
    );
  }
}

export function validateWeeklyBriefCompressionContract(fixture) {
  const outputs = fixture.fixture?.candidate_outputs || [];
  assert(outputs.length > 0, `${fixture.id}: compression candidates are missing`);
  const byName = new Map();
  for (const output of outputs) {
    validateBriefCompressionOutput(fixture, output);
    assert(!byName.has(output.name), `${fixture.id}: duplicate compression output ${output.name}`);
    byName.set(output.name, output);
  }

  for (const [baselineName, variantName] of fixture.fixture?.expected_same_body_pairs || []) {
    const baseline = byName.get(baselineName);
    const variant = byName.get(variantName);
    assert(baseline && variant, `${fixture.id}: unknown same-body comparison`);
    assert.equal(
      compressionBodyFingerprint(variant),
      compressionBodyFingerprint(baseline),
      `${fixture.id}: ${variantName} changed the body without changing management meaning`,
    );
  }
  for (const [baselineName, variantName] of fixture.fixture?.expected_different_body_pairs || []) {
    const baseline = byName.get(baselineName);
    const variant = byName.get(variantName);
    assert(baseline && variant, `${fixture.id}: unknown different-body comparison`);
    assert.notEqual(
      compressionBodyFingerprint(variant),
      compressionBodyFingerprint(baseline),
      `${fixture.id}: ${variantName} failed to surface a management change`,
    );
  }
  for (const [baselineName, variantName] of fixture.fixture?.expected_appendix_growth_pairs || []) {
    const baseline = byName.get(baselineName);
    const variant = byName.get(variantName);
    assert(baseline && variant, `${fixture.id}: unknown appendix-growth comparison`);
    assert(
      appendixSignalCount(variant) > appendixSignalCount(baseline),
      `${fixture.id}: ${variantName} did not preserve added accountability or evidence in the appendix`,
    );
  }
  const cards = fixture.fixture?.change_explanation_cards || [];
  for (const card of cards) validateChangeExplanationCard(fixture, card);
  validateChangeExplanationCardProbes(fixture, cards);
}

const FORBIDDEN_DECK_FIELDS = [
  'evidence_appendix',
  'evidence appendix',
  '证据附录',
  'internal_evidence',
  'audience takeaway',
  'recommended visual form',
  'page composition',
  'on-slide copy',
  'production constraints',
  'source grounding packet',
  'intended_takeaway',
  'supported_claim',
  'design_rationale',
  'problem_reframe',
  '"stories"',
  '"why"',
  '"goal"',
];

const FORBIDDEN_ROLE_TITLES = new Set([
  'background',
  'context',
  'design rationale',
  'implementation',
  'mechanism',
  'validation',
  '背景',
  '设计判断',
  '实现机制',
  '验证结果',
]);

function validatePptReadyMarkdownOutput(fixture, output) {
  const config = fixture.fixture || {};
  const audience = output.audience_contract || {};
  const slides = Array.isArray(output.slides) ? output.slides : [];
  const { internal_evidence, ...publicOutput } = output;
  const publicText = JSON.stringify(publicOutput).toLowerCase();
  for (const field of FORBIDDEN_DECK_FIELDS) {
    assert(!publicText.includes(field), `${fixture.id}: public deck leaks ${field}`);
  }

  if (config.expected_empty_state) {
    validateExpectedFraming(fixture, audience, config.expected_default_framing);
    for (const field of ['primary_audience', 'occasion', 'deck_job']) {
      assert(nonEmptyString(audience[field]), `${fixture.id}: empty-state audience contract ${field} is missing`);
    }
    assert.equal(slides.length, 0, `${fixture.id}: evidence-insufficient output must not contain slides`);
    assert.deepEqual(
      Object.keys(output).sort(),
      ['audience_contract', 'empty_state', 'slides'],
      `${fixture.id}: empty state contains unsupported deck fields`,
    );
    const emptyState = output.empty_state || {};
    assert(nonEmptyString(emptyState.reason), `${fixture.id}: empty-state reason is missing`);
    assert(nonEmptyStringArray(emptyState.missing_evidence), `${fixture.id}: empty-state missing evidence is absent`);
    assert(nonEmptyString(emptyState.next_action), `${fixture.id}: empty-state next action is missing`);
    if (config.expected_failure_type) {
      assert.equal(emptyState.heading, 'PPT Mode 未通过', `${fixture.id}: capability failure heading is wrong`);
      assert.equal(emptyState.failure_type, config.expected_failure_type, `${fixture.id}: capability failure type is wrong`);
      assert(nonEmptyStringArray(emptyState.candidate_lanes), `${fixture.id}: capability failure lost candidate lanes`);
      assert(nonEmptyStringArray(emptyState.usable_facts), `${fixture.id}: capability failure lost usable facts`);
      assert(nonEmptyStringArray(emptyState.evidence_boundaries), `${fixture.id}: capability failure lost evidence boundaries`);
      assert(nonEmptyStringArray(emptyState.next_options), `${fixture.id}: capability failure has no recovery options`);
      assert(!/slide\s*\d|第\s*\d\s*页/i.test(JSON.stringify(emptyState)), `${fixture.id}: capability failure masquerades as numbered slides`);
    }
    return;
  }

  for (const field of [
    'primary_audience',
    'prior_knowledge',
    'occasion',
    'deck_job',
    'audience_outcome',
    'central_claim',
    'confidence_boundary',
  ]) {
    assert(nonEmptyString(audience[field]), `${fixture.id}: audience contract ${field} is missing`);
  }
  assert(nonEmptyString(output.deck_context), `${fixture.id}: deck context is missing`);
  assert(nonEmptyString(output.management_question), `${fixture.id}: management question is missing`);
  assert(nonEmptyString(output.thesis), `${fixture.id}: deck thesis is missing`);
  assert(slides.length > 0, `${fixture.id}: main deck must contain at least one necessary slide`);
  if (Number.isInteger(fixture.fixture?.expected_slide_count)) {
    assert.equal(slides.length, fixture.fixture.expected_slide_count, `${fixture.id}: deck has the wrong merge/split result`);
  }

  const slideIds = new Set();
  for (const [slideIndex, slide] of slides.entries()) {
    const slideLabel = `${fixture.id}: slide ${slideIndex + 1}`;
    assert(nonEmptyString(slide.id), `${slideLabel} stable id is missing`);
    assert(!slideIds.has(slide.id), `${slideLabel} duplicates slide id ${slide.id}`);
    slideIds.add(slide.id);
    assert(nonEmptyString(slide.title), `${slideLabel} title is missing`);
    assert(nonEmptyString(slide.content), `${slideLabel} presentation content is missing`);
    assert(!/[?？]\s*$/.test(slide.title), `${slideLabel} uses a question instead of a supported claim`);
    assert(
      !FORBIDDEN_ROLE_TITLES.has(normalizeNarrativeText(slide.title)),
      `${slideLabel} title exposes an internal role`,
    );
    assert(!containsForbiddenMainDeckReference(slide.title), `${slideLabel} title contains an unsafe reference`);
    assert(
      !slide.content.replaceAll('\\n', '\n').split('\n').some((line) => containsForbiddenMainDeckReference(line)),
      `${slideLabel} content contains an unsafe reference`,
    );
    assert(
      !/(place on the left|use a .*diagram|font|color|layout|card grid|制作|版式|字体|颜色)/i.test(slide.content),
      `${slideLabel} contains production guidance`,
    );
    for (const term of fixture.fixture?.required_title_terms?.[slideIndex] || []) {
      assert(slide.title.toLowerCase().includes(term.toLowerCase()), `${slideLabel} title is missing claim term ${term}`);
    }
    for (const term of fixture.fixture?.required_content_terms?.[slideIndex] || []) {
      assert(slide.content.toLowerCase().includes(term.toLowerCase()), `${slideLabel} is missing grounded content term ${term}`);
    }
    const content = slide.content.replaceAll('\\n', '\n');
    const diagramIndex = content.search(/```(?:mermaid|text)\b/i);
    if (diagramIndex >= 0) {
      const introduction = content.slice(0, diagramIndex).trim();
      assert(nonEmptyString(introduction), `${slideLabel} must explain the concept before its diagram`);
      for (const term of fixture.fixture?.required_pre_diagram_terms?.[slideIndex] || []) {
        assert(
          introduction.toLowerCase().includes(String(term).toLowerCase()),
          `${slideLabel} diagram introduction is missing concept term ${term}`,
        );
      }
    }
    const mainText = `${slide.title}\n${slide.content}`.toLowerCase();
    for (const term of fixture.fixture?.forbidden_main_terms || []) {
      assert(!mainText.includes(String(term).toLowerCase()), `${slideLabel} leaked audience-inappropriate term ${term}`);
    }
  }

  const evidenceMap = Array.isArray(output.internal_evidence) ? output.internal_evidence : [];
  assert(evidenceMap.length > 0, `${fixture.id}: internal evidence map is missing`);
  const availableSourceRefs = new Set(config.available_source_refs || []);
  assert(availableSourceRefs.size > 0, `${fixture.id}: source allowlist is missing`);
  for (const item of evidenceMap) {
    assert(nonEmptyString(item.claim), `${fixture.id}: evidence map claim is missing`);
    assert(nonEmptyString(item.source), `${fixture.id}: evidence map source is missing`);
    assert(nonEmptyString(item.boundary), `${fixture.id}: evidence map boundary is missing`);
    const mappedSourceRefs = item.source.split(';').map(value => value.trim()).filter(Boolean);
    if (availableSourceRefs.size > 0) {
      for (const sourceRef of mappedSourceRefs) {
        assert(availableSourceRefs.has(sourceRef), `${fixture.id}: evidence map uses unavailable source ${sourceRef}`);
      }
    }
    if (config.require_claim_source_coverage) {
      assert(nonEmptyStringArray(item.slide_ids), `${fixture.id}: evidence map slide mapping is missing`);
      assert(nonEmptyString(item.proof_responsibility), `${fixture.id}: evidence map proof responsibility is missing`);
      assert(nonEmptyStringArray(item.source_refs), `${fixture.id}: evidence map source refs are missing`);
      for (const sourceRef of item.source_refs) {
        assert(availableSourceRefs.has(sourceRef), `${fixture.id}: evidence map uses unavailable source ${sourceRef}`);
        assert(mappedSourceRefs.includes(sourceRef), `${fixture.id}: mapped source omits grounded ref ${sourceRef}`);
        const contract = config.grounding_contracts?.[sourceRef];
        if (config.grounding_contracts) {
          assert(contract, `${fixture.id}: source ${sourceRef} has no grounding contract`);
          for (const term of contract.claim_terms || []) {
            assert(item.claim.includes(term), `${fixture.id}: source ${sourceRef} is attached to the wrong claim`);
          }
          for (const term of contract.boundary_terms || []) {
            assert(item.boundary.includes(term), `${fixture.id}: source ${sourceRef} has the wrong evidence boundary`);
          }
          const allowedSlideIds = new Set(contract.allowed_slide_ids || []);
          assert(
            item.slide_ids.every(slideId => allowedSlideIds.has(slideId)),
            `${fixture.id}: source ${sourceRef} is attached to the wrong slide`,
          );
        }
      }
    }
  }
  const evidenceText = evidenceMap.map(item => `${item.source}\n${item.boundary}`).join('\n').toLowerCase();
  for (const term of fixture.fixture?.required_internal_source_terms || []) {
    assert(
      evidenceText.includes(String(term).toLowerCase()),
      `${fixture.id}: internal evidence map is missing source-chain term ${term}`,
    );
  }

  for (const unique of fixture.fixture?.unique_content_terms || []) {
    const owners = slides.filter((slide) => slide.content.toLowerCase().includes(unique.toLowerCase()));
    assert.equal(owners.length, 1, `${fixture.id}: content unit ${unique} is missing or does not justify one page`);
  }

  if (config.require_claim_source_coverage) {
    const mappingsBySlide = new Map(slides.map(slide => [slide.id, []]));
    for (const item of evidenceMap) {
      for (const slideId of item.slide_ids) {
        assert(mappingsBySlide.has(slideId), `${fixture.id}: evidence map references unknown slide ${slideId}`);
        mappingsBySlide.get(slideId).push(item);
      }
    }
    for (const [slideId, mappings] of mappingsBySlide) {
      assert(mappings.length > 0, `${fixture.id}: slide ${slideId} has no claim-to-source mapping`);
    }
    if (config.require_distinct_slide_sources) {
      const sourceOwners = new Map();
      for (const [slideId, mappings] of mappingsBySlide) {
        const refs = new Set(mappings.flatMap(item => item.source_refs));
        assert(refs.size > 0, `${fixture.id}: slide ${slideId} has no source responsibility`);
        for (const sourceRef of refs) {
          const owners = sourceOwners.get(sourceRef) || [];
          owners.push(slideId);
          sourceOwners.set(sourceRef, owners);
        }
      }
      for (const [sourceRef, owners] of sourceOwners) {
        assert.equal(new Set(owners).size, 1, `${fixture.id}: source ${sourceRef} is reused across supposedly independent slides`);
      }
    }
  }

  if (config.require_distinct_slides) {
    const fingerprints = slides.map(slide => normalizeNarrativeText(`${slide.title}\n${slide.content}`));
    assert.equal(new Set(fingerprints).size, slides.length, `${fixture.id}: deck contains duplicate cognitive pages`);
  }

  if (config.independent_goal_lanes) {
    const lanes = config.independent_goal_lanes;
    assert(lanes.length > 1, `${fixture.id}: independent-goal benchmark needs multiple lanes`);
    assert.equal(slides[0].id, config.overview_slide_id, `${fixture.id}: multi-goal deck must start with the weekly goal map`);
    assert.equal(slides.at(-1).id, config.next_slide_id, `${fixture.id}: multi-goal deck must end with the grouped next-week plan`);
    assert.equal(output.thesis, config.expected_thesis, `${fixture.id}: multi-goal deck invented a shared business thesis`);
    assert.equal(slides[0].title, config.expected_overview_title, `${fixture.id}: weekly goal map title is unsupported`);
    assert.equal(slides[0].content, config.expected_overview_content, `${fixture.id}: weekly goal map contains unsupported claims`);
    const overviewText = `${slides[0].title}\n${slides[0].content}`.toLowerCase();
    const deckText = slides.map(slide => `${slide.title}\n${slide.content}`).join('\n').toLowerCase();
    for (const term of config.forbidden_common_goal_terms || []) {
      assert(!deckText.includes(String(term).toLowerCase()), `${fixture.id}: deck invented common goal ${term}`);
    }

    const ownedSlideIds = new Set();
    for (const lane of lanes) {
      for (const term of lane.overview_terms || []) {
        assert(overviewText.includes(String(term).toLowerCase()), `${fixture.id}: weekly goal map is missing ${lane.id} term ${term}`);
      }
      const allowedRefs = new Set(lane.allowed_source_refs || []);
      for (const slideId of lane.slide_ids || []) {
        assert(slideIds.has(slideId), `${fixture.id}: goal lane ${lane.id} has no dedicated narrative slide ${slideId}`);
        assert(!ownedSlideIds.has(slideId), `${fixture.id}: slide ${slideId} is shared across independent goal lanes`);
        ownedSlideIds.add(slideId);
        for (const item of evidenceMap.filter(entry => entry.slide_ids?.includes(slideId))) {
          for (const sourceRef of item.source_refs || []) {
            assert(allowedRefs.has(sourceRef), `${fixture.id}: goal lane ${lane.id} uses another lane's source ${sourceRef}`);
          }
        }
      }
      const overviewRefs = new Set(
        evidenceMap
          .filter(entry => entry.slide_ids?.includes(config.overview_slide_id))
          .flatMap(entry => entry.source_refs || []),
      );
      for (const sourceRef of lane.overview_source_refs || []) {
        assert(overviewRefs.has(sourceRef), `${fixture.id}: weekly goal map is missing ${lane.id} source ${sourceRef}`);
      }
      const finalSlideText = `${slides.at(-1).title}\n${slides.at(-1).content}`.toLowerCase();
      for (const term of lane.next_plan_terms || []) {
        assert(finalSlideText.includes(String(term).toLowerCase()), `${fixture.id}: next-week plan is missing ${lane.id} term ${term}`);
      }
    }
  }

  if (config.single_goal_direct_start) {
    assert.equal(slides[0].id, config.single_goal_direct_start.first_slide_id, `${fixture.id}: single-goal deck must start with its goal narrative`);
    const firstSlideText = `${slides[0].title}\n${slides[0].content}`.toLowerCase();
    for (const term of config.single_goal_direct_start.forbidden_overview_terms || []) {
      assert(!firstSlideText.includes(String(term).toLowerCase()), `${fixture.id}: single-goal deck added a generic overview`);
    }
  }

  if (config.expected_default_framing) {
    validateExpectedFraming(fixture, audience, config.expected_default_framing);
    const deckText = slides.map(slide => `${slide.title}\n${slide.content}`).join('\n').toLowerCase();
    for (const term of config.required_goal_terms || []) {
      assert(deckText.includes(String(term).toLowerCase()), `${fixture.id}: deck is missing goal grounding term ${term}`);
    }
    const finalSlideText = `${slides.at(-1).title}\n${slides.at(-1).content}`.toLowerCase();
    for (const term of config.required_next_plan_terms || []) {
      assert(finalSlideText.includes(String(term).toLowerCase()), `${fixture.id}: final slide is missing next-plan term ${term}`);
    }

    const sourceCommitments = new Map((config.source_next_commitments || []).map(item => [item.id, item]));
    const nextPlanItems = Array.isArray(output.next_plan_items) ? output.next_plan_items : [];
    assert(nextPlanItems.length > 0, `${fixture.id}: default team weekly has no structured next-plan items`);
    assert.equal(nextPlanItems.length, sourceCommitments.size, `${fixture.id}: next-plan commitments must be represented exactly once`);
    assert.equal(new Set(nextPlanItems.map(item => item.source_commitment_id)).size, nextPlanItems.length, `${fixture.id}: next-plan source commitments are duplicated`);
    const finalSlideBlocks = slides.at(-1).content.split(/\n\s*\n/).map(block => block.toLowerCase());
    for (const item of nextPlanItems) {
      const sourceItem = sourceCommitments.get(item.source_commitment_id);
      assert(sourceItem, `${fixture.id}: next-plan item ${item.id} has no source commitment`);
      assert.equal(item.commitment_state, sourceItem.commitment_state, `${fixture.id}: next-plan item ${item.id} changed commitment state`);
      assert.equal(item.statement, sourceItem.statement, `${fixture.id}: next-plan item ${item.id} changed its source statement`);
      assert.equal(item.closure_criterion, sourceItem.closure_criterion, `${fixture.id}: next-plan item ${item.id} changed its closure criterion`);
      const renderedStatement = `${sourceItem.rendered_prefix}${sourceItem.statement}`.toLowerCase();
      const renderedCriteria = (nonEmptyString(sourceItem.closure_criterion) ? [
        `通过标准：${sourceItem.closure_criterion}`,
        `通过标准是${sourceItem.closure_criterion}`,
        `通过标准是 ${sourceItem.closure_criterion}`,
      ] : ['通过标准未记录', '验收标准未记录'])
        .map(value => value.toLowerCase());
      assert(
        finalSlideBlocks.some(block => block.includes(renderedStatement) && renderedCriteria.some(value => block.includes(value))),
        `${fixture.id}: final slide does not render ${item.id} as one source-faithful commitment`,
      );
    }
  }
}

function validatePptRevisionRoundTrip(fixture, outputs) {
  const expectation = fixture.fixture?.revision_expectation;
  if (!expectation) return;
  assert.equal(outputs.length, 2, `${fixture.id}: revision benchmark requires baseline and revised outputs`);
  const [baseline, revised] = outputs;
  assert(nonEmptyString(baseline.version), `${fixture.id}: baseline version is missing`);
  assert(nonEmptyString(revised.version), `${fixture.id}: revised version is missing`);
  assert.notEqual(revised.version, baseline.version, `${fixture.id}: revision overwrote the baseline version`);
  assert.equal(revised.previous_version, baseline.version, `${fixture.id}: revised output does not point to its predecessor`);
  assert(Date.parse(revised.as_of) > Date.parse(baseline.as_of), `${fixture.id}: revision cutoff did not advance`);

  const baselineById = new Map(baseline.slides.map((slide) => [slide.id, slide]));
  const revisedById = new Map(revised.slides.map((slide) => [slide.id, slide]));
  const actualAdded = [...revisedById.keys()].filter(id => !baselineById.has(id)).sort();
  const actualRemoved = [...baselineById.keys()].filter(id => !revisedById.has(id)).sort();
  assert.deepEqual(actualAdded, [...(expectation.added_slide_ids || [])].sort(), `${fixture.id}: revision added unexpected slides`);
  assert.deepEqual(actualRemoved, [...(expectation.removed_slide_ids || [])].sort(), `${fixture.id}: revision removed unexpected slides`);
  if (expectation.expected_slide_order) {
    assert.deepEqual([...revisedById.keys()], expectation.expected_slide_order, `${fixture.id}: revised slide order is wrong`);
  }
  const changedSlideIds = expectation.changed_slide_ids || [];
  const unchangedSlideIds = expectation.unchanged_slide_ids || [];
  assert.equal(new Set(changedSlideIds).size, changedSlideIds.length, `${fixture.id}: changed slide classification contains duplicates`);
  assert.equal(new Set(unchangedSlideIds).size, unchangedSlideIds.length, `${fixture.id}: unchanged slide classification contains duplicates`);
  const classifiedSlideIds = [...changedSlideIds, ...unchangedSlideIds];
  assert.equal(new Set(classifiedSlideIds).size, classifiedSlideIds.length, `${fixture.id}: a slide is classified as both changed and unchanged`);
  const commonSlideIds = [...baselineById.keys()].filter(id => revisedById.has(id)).sort();
  assert.deepEqual([...classifiedSlideIds].sort(), commonSlideIds, `${fixture.id}: every slide shared by both versions must be classified exactly once`);

  for (const slideId of changedSlideIds) {
    assert(baselineById.has(slideId) && revisedById.has(slideId), `${fixture.id}: changed slide ${slideId} must exist in both versions`);
    assert.notDeepEqual(
      normalizeSemanticValue(revisedById.get(slideId)),
      normalizeSemanticValue(baselineById.get(slideId)),
      `${fixture.id}: affected slide ${slideId} was not substantively revised`,
    );
  }
  for (const slideId of unchangedSlideIds) {
    assert(baselineById.has(slideId) && revisedById.has(slideId), `${fixture.id}: unchanged slide ${slideId} must exist in both versions`);
    assert.deepEqual(
      normalizeSemanticValue(revisedById.get(slideId)),
      normalizeSemanticValue(baselineById.get(slideId)),
      `${fixture.id}: unrelated slide ${slideId} changed`,
    );
  }
  for (const [slideId, terms] of Object.entries(expectation.required_revised_terms || {})) {
    const slide = revisedById.get(slideId);
    assert(slide, `${fixture.id}: revised slide ${slideId} is missing`);
    const text = `${slide.title}\n${slide.content}`.toLowerCase();
    for (const term of terms) {
      assert(text.includes(String(term).toLowerCase()), `${fixture.id}: revised slide ${slideId} is missing ${term}`);
    }
  }
  for (const [slideId, terms] of Object.entries(expectation.forbidden_revised_terms || {})) {
    const slide = revisedById.get(slideId);
    assert(slide, `${fixture.id}: revised slide ${slideId} is missing`);
    const text = `${slide.title}\n${slide.content}`.toLowerCase();
    for (const term of terms) {
      assert(!text.includes(String(term).toLowerCase()), `${fixture.id}: revised slide ${slideId} retained ${term}`);
    }
  }
  for (const [slideId, terms] of Object.entries(expectation.required_revised_evidence || {})) {
    const evidence = (revised.internal_evidence || [])
      .filter(item => item.slide_ids?.includes(slideId))
      .map(item => `${item.claim}\n${item.source}\n${item.boundary}`)
      .join('\n')
      .toLowerCase();
    assert(nonEmptyString(evidence), `${fixture.id}: revised slide ${slideId} has no mapped evidence`);
    for (const term of terms) {
      assert(evidence.includes(String(term).toLowerCase()), `${fixture.id}: revised slide ${slideId} retained stale evidence`);
    }
  }
  if (actualAdded.length || actualRemoved.length || changedSlideIds.length) {
    assert.notDeepEqual(
      normalizeSemanticValue(revised.internal_evidence),
      normalizeSemanticValue(baseline.internal_evidence),
      `${fixture.id}: revised claims retained a stale internal evidence map`,
    );
  }
}

function validatePptRevisionRejectionProbes(fixture, outputs) {
  const expectation = fixture.fixture?.revision_expectation;
  if (!expectation) return;
  for (const probe of fixture.fixture?.revision_rejection_probes || []) {
    const mutantFixture = structuredClone(fixture);
    const mutantOutputs = structuredClone(outputs);
    const mutantExpectation = mutantFixture.fixture.revision_expectation;
    const [baseline, revised] = mutantOutputs;
    const baselineById = new Map(baseline.slides.map(slide => [slide.id, slide]));

    if (probe === 'whitespace-only') {
      revised.slides = revised.slides.map((slide) => {
        if (!(mutantExpectation.changed_slide_ids || []).includes(slide.id)) return slide;
        const original = structuredClone(baselineById.get(slide.id));
        original.content = `  ${original.content.replaceAll('\n', '  \n')}  `;
        return original;
      });
    } else if (probe === 'unclassified-common-slide') {
      mutantExpectation.changed_slide_ids = mutantExpectation.changed_slide_ids.slice(1);
    } else if (probe === 'duplicate-classification') {
      const slideId = mutantExpectation.changed_slide_ids[0] || mutantExpectation.unchanged_slide_ids[0];
      mutantExpectation.unchanged_slide_ids.push(slideId);
    } else if (probe === 'nonexistent-classification') {
      mutantExpectation.changed_slide_ids.push('missing-slide');
    } else if (probe === 'stale-internal-evidence') {
      revised.internal_evidence = structuredClone(baseline.internal_evidence);
      revised.internal_evidence[0].boundary += ' Irrelevant wording changed.';
    } else {
      throw new Error(`${fixture.id}: unknown revision rejection probe ${probe}`);
    }

    assert.throws(
      () => validatePptRevisionRoundTrip(mutantFixture, mutantOutputs),
      `${fixture.id}: revision rejection probe ${probe} unexpectedly passed`,
    );
  }
}

export function validateWeeklyPptReadyMarkdownContract(fixture) {
  const outputs = fixture.fixture?.candidate_outputs || [fixture.fixture?.candidate_output || {}];
  for (const output of outputs) validatePptReadyMarkdownOutput(fixture, output);
  validatePptRevisionRoundTrip(fixture, outputs);
  validatePptRevisionRejectionProbes(fixture, outputs);
}

export function validateWeeklyPptReadyMarkdownRejectionProbes(fixture) {
  for (const probe of fixture.fixture?.rejection_probes || []) {
    const mutant = structuredClone(fixture);
    mutant.id = `${fixture.id}:${probe}`;
    const output = mutant.fixture.candidate_output || mutant.fixture.candidate_outputs[0];
    const slides = output.slides;

    if (probe === 'missing-audience') {
      output.audience_contract.primary_audience = '';
    } else if (probe === 'missing-outcome') {
      output.audience_contract.audience_outcome = '';
    } else if (probe === 'missing-thesis') {
      output.thesis = '';
    } else if (probe === 'missing-content') {
      slides[0].content = '';
    } else if (probe === 'empty-deck') {
      output.slides = [];
    } else if (probe === 'diagram-first') {
      const content = slides[0].content.replaceAll('\\n', '\n');
      const diagramIndex = content.search(/```(?:mermaid|text)\b/i);
      slides[0].content = content.slice(diagramIndex);
    } else if (probe === 'production-guideline') {
      slides[0].content += '\n\n### Page composition\nPlace nodes on the left using blue cards.';
    } else if (probe === 'topic-title') {
      slides[0].title = 'Provider comparison';
    } else if (probe === 'question-title') {
      slides[0].title = 'Which provider should we choose?';
    } else if (probe === 'claim-proof-gap') {
      slides[0].content = 'Implementation work was completed during the week.';
    } else if (probe === 'role-title') {
      slides[0].title = '设计判断';
    } else if (probe === 'unsafe-main-deck-reference') {
      slides[0].content += '\n/Users/example/private/design.md';
    } else if (probe === 'complex-result-merged') {
      slides[0].content += `\n${slides[1].content}`;
      slides.splice(1);
    } else if (probe === 'simple-result-split') {
      const original = slides[0];
      slides.splice(
        0,
        1,
        {...original, id: `${original.id}-before`, title: 'The previous handoff had two owners'},
        {...original, id: `${original.id}-after`, title: 'The new handoff has one owner'},
      );
    } else if (probe === 'wrong-default-audience') {
      output.audience_contract.primary_audience = '负责拍板的项目经理';
    } else if (probe === 'invented-duration') {
      output.audience_contract.duration = '5 分钟';
    } else if (probe === 'wrong-prior-knowledge') {
      output.audience_contract.prior_knowledge = '完全不了解项目背景';
    } else if (probe === 'missing-goal-grounding') {
      for (const slide of slides) {
        slide.title = slide.title.replaceAll('目标', '事项');
        slide.content = slide.content.replaceAll('目标', '事项').replaceAll('可复现', '可用');
      }
    } else if (probe === 'missing-next-plan') {
      slides.pop();
    } else if (probe === 'negated-next-plan') {
      const statement = output.next_plan_items[0].statement;
      slides.at(-1).content = slides.at(-1).content.replace(statement, `不${statement}`);
    } else if (probe === 'omitted-next-plan-item') {
      output.next_plan_items.pop();
    } else if (probe === 'swapped-next-plan-provenance') {
      const [first, second] = output.next_plan_items;
      [first.source_commitment_id, second.source_commitment_id] = [second.source_commitment_id, first.source_commitment_id];
    } else if (probe === 'fabricated-confirmed-plan') {
      output.next_plan_items.find(item => item.commitment_state === 'proposed').commitment_state = 'confirmed';
    } else if (probe === 'fake-source') {
      output.internal_evidence[0].source_refs = ['nonexistent:made-up'];
    } else if (probe === 'fake-visible-source') {
      output.internal_evidence[0].source = 'nonexistent:made-up';
    } else if (probe === 'swapped-source-responsibility') {
      const [first, second] = output.internal_evidence;
      [first.source, second.source] = [second.source, first.source];
      [first.source_refs, second.source_refs] = [second.source_refs, first.source_refs];
    } else if (probe === 'duplicate-pages') {
      const first = slides[0];
      output.slides = slides.map((slide, index) => ({...first, id: `duplicate-${index}`}));
    } else if (probe === 'forced-common-goal') {
      output.slides[0].content += `\n共同目标：提升项目质量。`;
    } else if (probe === 'overview-missing-second-lane') {
      output.slides[0].content = '分镜质量：让质量问题可定位；职责边界已收敛，routing 未证明收益。';
    } else if (probe === 'second-lane-plan-only') {
      output.slides = slides.filter(slide => slide.id !== 'agent-native-path');
      output.slides[0].content = '分镜质量：让质量问题可定位；职责边界已收敛，routing 未证明收益。';
    } else if (probe === 'second-lane-internal-only') {
      output.slides = slides.filter(slide => slide.id !== 'agent-native-path');
      output.slides[0].content = '分镜质量：让质量问题可定位；职责边界已收敛，routing 未证明收益。';
      output.slides.at(-1).content = '分镜质量｜Proposed：补齐 cleanup 归因；通过标准：拆出净贡献。';
    } else if (probe === 'cross-lane-source') {
      const item = output.internal_evidence.find(entry => entry.slide_ids?.includes('agent-native-path'));
      item.source = 'raw:quality-objective';
      item.source_refs = ['raw:quality-objective'];
    } else if (probe === 'overview-without-why') {
      output.slides[0].content = '分镜质量：进行中；Agent-native：进行中。';
    } else if (probe === 'unsupported-overview-claim') {
      output.slides[0].content += '\n两条主线都已生产上线。';
    } else if (probe === 'swapped-slide-grounding') {
      const quality = output.internal_evidence.find(item => item.slide_ids?.includes('quality-eval'));
      const agent = output.internal_evidence.find(item => item.slide_ids?.includes('agent-native-path'));
      [quality.slide_ids, agent.slide_ids] = [agent.slide_ids, quality.slide_ids];
    } else if (probe === 'generic-grounding-text') {
      for (const item of output.internal_evidence) {
        item.claim = 'generic claim';
        item.boundary = 'generic boundary';
      }
    } else if (probe === 'mechanical-one-page-per-lane') {
      const qualityBoundary = output.slides.find(slide => slide.id === 'quality-boundary');
      const qualityEval = output.slides.find(slide => slide.id === 'quality-eval');
      qualityBoundary.content += `\n${qualityEval.content}`;
      output.slides = output.slides.filter(slide => slide.id !== 'quality-eval');
    } else if (probe === 'internal-coverage-ledger') {
      output.slides[1].content += '\nCoverage ledger: remaining cards use explicit exclusion.';
    } else if (probe === 'undefined-stage-labels') {
      output.slides[1].content = 'B0–B3 已完成职责划分，但具体对象无需在页面解释。';
    } else if (probe === 'implementation-inventory') {
      output.slides[1].content = '309 行收敛到 92 行，harness 4/4，并覆盖 cache、force、override 与 hook。';
    } else if (probe === 'single-goal-overview') {
      output.slides[0].title = '本周目标与进度总览：可复现召回边界';
      output.slides[0].content = '目标：让召回结果可复现。最终选择固定边界，原因是先统一执行语义。';
    } else if (probe === 'empty-state-with-slide') {
      output.slides = [{id: 'invented', title: 'Invented slide', content: 'No evidence.'}];
    } else if (probe === 'empty-state-missing-repair') {
      output.empty_state.next_action = '';
    } else if (probe === 'empty-state-leaks-deck') {
      output.supported_claim = 'invented';
      output.internal_evidence = [{claim: 'fake', source: 'fake', boundary: 'fake'}];
    } else if (probe === 'empty-state-wrong-framing') {
      output.audience_contract.primary_audience = '负责拍板的项目经理';
      output.audience_contract.duration = '5 分钟';
    } else if (probe === 'capability-failure-missing-lanes') {
      output.empty_state.candidate_lanes = [];
    } else if (probe === 'capability-failure-numbered-content') {
      output.empty_state.usable_facts[0] = 'Slide 1: implementation inventory';
    } else {
      throw new Error(`${fixture.id}: unknown PPT-ready Markdown rejection probe ${probe}`);
    }

    assert.throws(
      () => validatePptReadyMarkdownOutput(mutant, output),
      `${fixture.id}: PPT-ready Markdown rejection probe ${probe} unexpectedly passed`,
    );
  }
}

function validateSourceGroundingRecoveryOutput(fixture, output) {
  const config = fixture.fixture || {};
  const gaps = Array.isArray(output.gaps) ? output.gaps : [];
  const questions = Array.isArray(output.questions) ? output.questions : [];
  const requested = gaps.filter(gap => gap.action === 'request_source');
  assert(gaps.length > 0, `${fixture.id}: source recovery has no grounding gaps`);
  assert.equal(new Set(gaps.map(gap => gap.id)).size, gaps.length, `${fixture.id}: source gap ids must be unique`);
  if (config.expected_material_gap_ids) {
    assert.deepEqual(
      gaps.filter(gap => gap.material_to_main_deck).map(gap => gap.id).sort(),
      [...config.expected_material_gap_ids].sort(),
      `${fixture.id}: material source gaps were self-classified incorrectly`,
    );
  }
  if (config.expected_exact_gap_ids) {
    assert.deepEqual(
      gaps.filter(gap => gap.requires_exact_grounding).map(gap => gap.id).sort(),
      [...config.expected_exact_gap_ids].sort(),
      `${fixture.id}: exact grounding gaps were self-classified incorrectly`,
    );
  }
  assert(questions.length <= 1, `${fixture.id}: material source gaps must be batched into one question`);
  if (requested.length) {
    assert.equal(questions.length, 1, `${fixture.id}: material source gaps need one recovery question`);
    assert(nonEmptyString(questions[0].text), `${fixture.id}: recovery question has no user-facing text`);
    assert.deepEqual(
      [...questions[0].gap_ids].sort(),
      requested.map(gap => gap.id).sort(),
      `${fixture.id}: recovery question does not cover every requested source`,
    );
    for (const gap of requested) {
      for (const value of [gap.claim, gap.missing, gap.skip_outcome, ...gap.accepted_source_forms]) {
        assert(questions[0].text.includes(value), `${fixture.id}: recovery question omits ${gap.id} context`);
      }
    }
  } else {
    assert.equal(questions.length, 0, `${fixture.id}: recovery question remained after all requests were removed`);
  }
  for (const gap of gaps) {
    assert(nonEmptyString(gap.id), `${fixture.id}: source gap id is missing`);
    assert(nonEmptyString(gap.claim), `${fixture.id}: source gap claim is missing`);
    assert(nonEmptyString(gap.missing), `${fixture.id}: source gap description is missing`);
    assert(nonEmptyString(gap.skip_outcome), `${fixture.id}: source gap skip outcome is missing`);
    assert(['request_source', 'omit', 'conceptual_only', 'fail_ppt'].includes(gap.action), `${fixture.id}: source gap action is invalid`);
    assert(['omit', 'conceptual_only', 'fail_ppt'].includes(gap.degrade_action), `${fixture.id}: source gap degradation is invalid`);
    if (!gap.material_to_main_deck) {
      assert(['omit', 'conceptual_only'].includes(gap.action), `${fixture.id}: appendix-only source gap interrupted the user`);
    }
    if (gap.requires_exact_grounding && gap.summary_insufficient && gap.material_to_main_deck) {
      assert(
        ['request_source', 'fail_ppt'].includes(gap.action),
        `${fixture.id}: exact material grounding was silently approximated`,
      );
    }
    if (gap.action === 'request_source') {
      assert(nonEmptyStringArray(gap.accepted_source_forms), `${fixture.id}: recovery request has no accepted source forms`);
    }
  }
  const treatments = Array.isArray(output.supplied_source_treatments) ? output.supplied_source_treatments : [];
  assert.equal(new Set(treatments.map(item => item.source_type)).size, treatments.length, `${fixture.id}: supplied source types must be unique`);
  const expectedResponsibilities = config.expected_source_responsibilities || {};
  if (Object.keys(expectedResponsibilities).length) {
    assert.deepEqual(
      treatments.map(item => item.source_type).sort(),
      Object.keys(expectedResponsibilities).sort(),
      `${fixture.id}: supplied source treatments are incomplete`,
    );
  }
  for (const treatment of treatments) {
    assert(nonEmptyString(treatment.source_type), `${fixture.id}: supplied source type is missing`);
    assert(nonEmptyString(treatment.proof_responsibility), `${fixture.id}: supplied source responsibility is missing`);
    if (expectedResponsibilities[treatment.source_type]) {
      assert.equal(
        treatment.proof_responsibility,
        expectedResponsibilities[treatment.source_type],
        `${fixture.id}: ${treatment.source_type} has the wrong proof responsibility`,
      );
    }
  }
}

export function validateWeeklySourceGroundingRecoveryContract(fixture) {
  const baseline = structuredClone(fixture.fixture?.candidate_output || {});
  validateSourceGroundingRecoveryOutput(fixture, baseline);
  for (const probe of fixture.fixture?.rejection_probes || []) {
    const output = structuredClone(baseline);
    if (probe === 'ask-for-nonmaterial-source') {
      output.gaps.find(gap => !gap.material_to_main_deck).action = 'request_source';
    } else if (probe === 'split-recovery-questions') {
      const ids = output.questions[0].gap_ids;
      output.questions = ids.map(id => ({gap_ids: [id]}));
    } else if (probe === 'verbal-code-grounding') {
      output.supplied_source_treatments.find(item => item.source_type === 'user_explanation').proof_responsibility = 'committed_structure';
    } else if (probe === 'skipped-exact-architecture') {
      output.gaps.find(gap => gap.requires_exact_grounding).degrade_action = 'precise_architecture';
    } else if (probe === 'missing-recovery-impact') {
      output.gaps.find(gap => gap.action === 'request_source').skip_outcome = '';
    } else if (probe === 'self-classified-material-gaps') {
      for (const gap of output.gaps.filter(item => item.material_to_main_deck)) {
        gap.material_to_main_deck = false;
        gap.requires_exact_grounding = false;
        gap.action = 'omit';
      }
      output.questions = [];
    } else if (probe === 'opaque-recovery-question') {
      output.questions[0].text = '?';
    } else if (probe === 'missing-source-treatments') {
      output.supplied_source_treatments = [];
    } else if (probe === 'wrong-screenshot-responsibility') {
      output.supplied_source_treatments.find(item => item.source_type === 'screenshot').proof_responsibility = 'committed_structure';
    } else if (probe === 'stale-recovery-question') {
      for (const gap of output.gaps.filter(item => item.action === 'request_source')) gap.action = 'fail_ppt';
    } else {
      throw new Error(`${fixture.id}: unknown source recovery rejection probe ${probe}`);
    }
    assert.throws(
      () => validateSourceGroundingRecoveryOutput(fixture, output),
      `${fixture.id}: source recovery rejection probe ${probe} unexpectedly passed`,
    );
  }
}
