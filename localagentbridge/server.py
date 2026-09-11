from typing import Annotated, Literal
from mcp.server.fastmcp import FastMCP
from mcp.types import CallToolResult, TextContent, ToolAnnotations
from pydantic import Field
from .bridge import BridgeError
from .schemas import SourceFile, Feedback, RoutingHints, compact
from .service import Service

Text = Annotated[str, Field(max_length=24000)]
Task = Annotated[str, Field(max_length=2000)]
Paths = Annotated[list[Annotated[str, Field(max_length=240)]], Field(max_length=20)]
Role = Literal['general', 'coding', 'reasoning']


def create_server(config):
    service = Service(config)
    mcp = FastMCP('LocalAgentBridge', instructions='Use find_relevant_context before loading repository files. Local results are advisory. Keep important decisions with Codex; report outcomes through triage_task feedback.')
    annotations = ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False)

    async def invoke(awaitable):
        try:
            result = await awaitable
            return CallToolResult(content=[TextContent(type='text', text=compact(result))])
        except (BridgeError, ValueError) as e:
            return CallToolResult(isError=True, content=[TextContent(type='text', text=compact({'error': str(e)[:400]}))])

    @mcp.tool(annotations=annotations)
    async def find_relevant_context(task: Annotated[str, Field(min_length=1, max_length=2000)],
                                    scope: Annotated[str, Field(max_length=240)] = '', use_model: bool = True,
                                    routing: RoutingHints | None = None) -> CallToolResult:
        """Search configured repository locally; return verified files/symbols/line excerpts. Optional model ranking, no editing."""
        return await invoke(service.find_context(task, scope, use_model, routing))

    @mcp.tool(annotations=annotations)
    async def summarize_context(task: Annotated[str, Field(min_length=1, max_length=2000)], text: Text = '',
                                files: Annotated[list[SourceFile], Field(max_length=20)] | None = None,
                                file_paths: Paths | None = None, routing: RoutingHints | None = None) -> CallToolResult:
        """Compress supplied content or relative file paths under source_root. Prefer paths to avoid cloud context."""
        return await invoke(service.analyze('summarize_context', text, task, files=files, file_paths=file_paths, routing=routing))

    @mcp.tool(annotations=annotations)
    async def analyze_code(task: Task = 'Explain behavior, defects and tests.', text: Text = '', file_paths: Paths | None = None,
                           routing: RoutingHints | None = None) -> CallToolResult:
        """Analyze supplied code or selected files using the coding role; return bounded findings for Codex to verify."""
        return await invoke(service.analyze('analyze_code', text, task, file_paths=file_paths, routing=routing))

    @mcp.tool(annotations=annotations)
    async def analyze_test_output(output: Text = '', file_paths: Paths | None = None, routing: RoutingHints | None = None) -> CallToolResult:
        """Triage supplied test/build output or saved log files locally; never run tests or commands."""
        return await invoke(service.analyze('analyze_test_output', output, file_paths=file_paths, routing=routing))

    @mcp.tool(annotations=annotations)
    async def review_diff(diff: Text = '', task: Task = '', file_paths: Paths | None = None, routing: RoutingHints | None = None) -> CallToolResult:
        """First-pass review of supplied diff or saved patch file. Code changes remain Codex's responsibility."""
        return await invoke(service.analyze('review_diff', diff, task, file_paths=file_paths, routing=routing))

    @mcp.tool(annotations=annotations)
    async def triage_task(task: Task = '', context_chars: Annotated[int, Field(ge=0, le=10000000)] = 0,
                          file_count: Annotated[int, Field(ge=0, le=100000)] = 0,
                          risk: Literal['low', 'medium', 'high'] = 'low',
                          feedback: Annotated[list[Feedback], Field(max_length=20)] | None = None,
                          confidence: Literal['low', 'medium', 'high'] = 'high',
                          complexity: Literal['simple', 'moderate', 'complex'] = 'simple',
                          ambiguous: bool = False,
                          capability: Literal['analysis', 'implementation', 'architecture', 'orchestration', 'disagreement', 'execution'] = 'analysis',
                          failed_local_attempts: Annotated[int, Field(ge=0, le=100)] = 0) -> CallToolResult:
        """Local-first advisory gate. Supply known risk/complexity, ambiguity, capability and failed attempts. Small routine tasks go directly to local tools. Feedback-only uses no LLM."""
        return await invoke(service.triage(task, context_chars, file_count, risk, feedback, confidence=confidence,
                            complexity=complexity, ambiguous=ambiguous, capability=capability, failed_local_attempts=failed_local_attempts))

    @mcp.tool(annotations=annotations)
    async def second_opinion(question: Annotated[str, Field(min_length=1, max_length=2000)], context: Text = '',
                             file_paths: Paths | None = None, consensus: bool = False,
                             roles: Annotated[list[Role], Field(max_length=3)] | None = None, routing: RoutingHints | None = None) -> CallToolResult:
        """Assess a proposal locally. Optional consensus asks 2-3 configured models independently, once each, sequentially."""
        return await invoke(service.second_opinion(question, context, file_paths, consensus, roles, routing))

    return mcp
