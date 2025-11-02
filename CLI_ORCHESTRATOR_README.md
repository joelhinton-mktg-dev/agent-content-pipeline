# CLI Pipeline Orchestrator - WebADK Proven Pattern Implementation

## Overview

The `pipeline_orchestrator_cli.py` implements the **proven webADK subprocess pattern** that successfully handles multi-agent workflow orchestration where previous attempts failed.

## Key Success Factors

### ✅ External CLI Execution
- Uses `subprocess` with `cat temp_file | timeout 300 adk run agent_name`
- Each agent runs in isolated ADK CLI session
- No dependency on internal ADK Python APIs

### ✅ Explicit Data Passing
- Embeds previous stage results directly in prompts
- No reliance on ADK context state or session management
- Handles 64K+ content without issues

### ✅ Robust Process Management
- 300-second timeout per agent via `timeout` command
- Additional 320-second `asyncio.wait_for()` safety net
- Proper subprocess monitoring and cleanup

### ✅ Enhanced Output Cleaning
- Filters out ADK system messages and logging noise
- Multiple fallback strategies for content extraction
- Returns clean agent responses only

## Architecture

```
User Input → Temp File → subprocess 'adk run' → Output Cleaning → Next Stage
```

### Stage Flow
1. **Outline Generation** → Clean outline result
2. **Content Creation** → Uses outline in prompt → Clean content result  
3. **SEO Optimization** → Uses content in prompt → Clean SEO result
4. **Publication Package** → Uses content + SEO in prompt → Final package

## Usage

```bash
python3 pipeline_orchestrator_cli.py
```

Enter topic when prompted, and the pipeline will:
- Generate comprehensive outline
- Create detailed content based on outline
- Perform SEO optimization on content
- Create WordPress publication package

## Key Improvements Over Failed Attempts

| Issue | Old Approach | New Solution |
|-------|-------------|--------------|
| Stage 2→3 Handoff | ADK context.state | Direct prompt embedding |
| Agent Communication | Python imports + invoke() | External CLI subprocess |
| 64K Content Handling | Context state limits | CLI can handle large prompts |
| Process Hanging | Internal ADK APIs hang | Timeout-controlled subprocess |
| Output Extraction | Unclear response handling | Proven cleaning strategy |

## Files

- `pipeline_orchestrator_cli.py` - Main CLI orchestrator
- `test_cli_pipeline.py` - Test suite
- `verify_cli_implementation.py` - Implementation verification

## Why This Works

The CLI orchestrator succeeds because it treats ADK agents as **external tools** rather than Python library components. This matches how webADK operates and provides the stable, proven execution environment that ADK CLI was designed for.

## Technical Details

### Agent Execution Pattern
```python
async def run_agent_via_cli(self, agent_name, prompt):
    # Write prompt to temp file
    temp_file = f"/tmp/prompt_{agent_name}_{timestamp}.txt"
    with open(temp_file, 'w') as f:
        f.write(prompt)
    
    # Execute with timeout
    cmd = f"cat {temp_file} | timeout 300 adk run {agent_name}"
    proc = await asyncio.create_subprocess_shell(cmd, ...)
    
    # Clean and return output
    return self.clean_adk_output(stdout)
```

### Data Flow Example
```python
# Stage 2: Content Creation
content_prompt = f"""Write comprehensive article based on outline:

OUTLINE:
{outline_result}

INSTRUCTIONS:
- Write full sections for each heading
- Include statistics and examples
- Add image placeholders
...
"""
```

This approach **eliminates** the Stage 2→3 handoff failure and provides reliable multi-agent orchestration.