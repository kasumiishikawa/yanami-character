export const meta = {
  name: 'extract-yanami-traits',
  description: 'Extract Yanami Anna character traits from all 452 candidate scenes in parallel batches',
  phases: [
    { title: 'Extract', detail: 'Each agent reads a batch and writes analysis JSONL' },
    { title: 'Verify', detail: 'Confirm all batch analyses were written' },
  ],
}

phase('Extract')

const PROMPT_PATH = 'D:\\character\\prompts\\extract_yanami_scene.md'
const ANALYSIS_DIR = 'D:\\character\\data\\extracted\\analysis'
const BATCH_PREFIX = 'D:\\character\\data\\extracted\\batches\\batch_'

log('Starting parallel extraction of all 31 batches...')
log('Each agent reads its batch + the extraction prompt, then writes analysis to analysis dir.')

// Create analysis directory by spawning a quick agent that runs Write for each batch
// Actually, we'll have each batch-processing agent also write its own result.

const BATCH_COUNT = 31
const batchTasks = []

for (let i = 1; i <= BATCH_COUNT; i++) {
  const num = String(i).padStart(3, '0')
  const batchPath = `${BATCH_PREFIX}${num}.json`
  const outputPath = `${ANALYSIS_DIR}\\batch_${num}_analysis.json`

  batchTasks.push(() =>
    agent(`You are a light novel character analysis assistant. Your job is to extract structured character information about "八奈见杏菜" from scenes.

## Instructions
1. Read the extraction prompt from: ${PROMPT_PATH}
2. Read the batch data from: ${batchPath}
3. The batch file is JSON with a "scenes" array. For EACH scene, produce a structured analysis following the prompt's schema.
4. After analysis, use the Write tool to write the results to: ${outputPath}
   - The file should contain a JSON ARRAY of analysis objects (one per scene)
   - Each element follows the schema from the extraction prompt

## Writing the file
Use the Write tool to write the file at: ${outputPath}
Content: a JSON array, pretty-printed with indent=2, ensure_ascii=false.

## Quality rules
- If a scene only mentions the name without useful info, set "useful": false
- Be evidence-based — every claim must come from the text
- Distinguish: facts, speech patterns, behavior patterns, emotional states
- Cover surface/real emotion gaps, relationship dynamics, defense mechanisms`,
      { label: `batch-${num}`, phase: 'Extract' })
  )
}

const results = await parallel(batchTasks)

phase('Verify')

let success = 0
let failed = 0
for (let i = 0; i < results.length; i++) {
  if (results[i] === null) {
    failed++
    log(`Batch ${i+1}: FAILED (null result)`)
  } else {
    success++
  }
}

log(`\n===== EXTRACTION COMPLETE =====`)
log(`Successful: ${success}/${BATCH_COUNT}`)
log(`Failed: ${failed}`)
log(`Analysis files written to: ${ANALYSIS_DIR}`)
log(`\nNext step: run the merge script to combine all batch analyses into yanami_scene_analysis.jsonl`)

return {
  status: 'complete',
  total_batches: BATCH_COUNT,
  successful: success,
  failed: failed,
  analysis_dir: ANALYSIS_DIR,
}
