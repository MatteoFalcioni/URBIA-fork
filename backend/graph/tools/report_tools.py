from typing_extensions import Annotated
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from langgraph.types import interrupt

@tool
def write_report_tool(
    report_title: Annotated[str, "The title of the report"],
    report_content: Annotated[str, "The content of the report"],
    runtime: ToolRuntime
)->Command:
    """
    Write a report of the analysis performed.
    Interrupts the model to ask for approval before writing the report.
    """
    print("***writing report in write_report_tool")

    # refine this message in frontend and simplify it here in backend (the user will not see this below)
    response = interrupt(f"The model has finished its analysis and wants to write a report. To continue, input 'yes'. To reject, input 'no'.")

    if response["type"] == "accept":
        print("***accepted write report in write_report_tool")
        pass  # accepted write report: therefore, continue flow 
    elif response["type"] == "reject":
        print("***rejected write report in write_report_tool")
        return Command(update={
            "messages": [
                ToolMessage(
                    content="Report writing rejected by the user.", 
                    tool_call_id=runtime.tool_call_id
                )], 
            })  

    report_dict = {report_title: report_content}  

    return Command(  
        update = {
            "messages" : [ToolMessage(content="Report written successfully.", tool_call_id=runtime.tool_call_id)],
            "reports" : report_dict,
            "last_report_title" : report_title,
        }
    )

@tool
def write_source_tool(dataset_id: Annotated[str, "the dataset_id, i.e. the source"], runtime: ToolRuntime) -> Command:
    """
    Write a source to the list of sources. If the dataset is already in the list, returns a message that says so.
    """
    state = runtime.state
    sources = state["sources"]
    if dataset_id not in sources:
        sources_update = [dataset_id]
        return Command(update={"messages" : [ToolMessage(content=f"Dataset {dataset_id} added to sources.", tool_call_id=runtime.tool_call_id)], "sources" : sources_update})
    else:
        return Command(update={"messages" : [ToolMessage(content=f"Dataset {dataset_id} already in sources.", tool_call_id=runtime.tool_call_id)]})

