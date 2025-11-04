from typing_extensions import Annotated
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

@tool(
    name_or_callable="assign_to_report_writer",
    description="Use this to assign the task to the report writer when analysis is complete."
)
def assign_to_report_writer(
    reason: Annotated[str, "Brief reason why analysis is complete and report should be written"],
    runtime: ToolRuntime
) -> Command:
    """
    Assigns the task to the report writer when analysis is complete. 
    Since literal tool assingment was not working, we use this to update the state flag and conditional edge to route to the report writer.
    """
    
    return Command(
        update={
            "messages": [ToolMessage(
                content=f"Analysis complete. {reason}. Assigning to report writer.", 
                tool_call_id=runtime.tool_call_id
            )],
            "write_report" : True
        }
    )


from langgraph.types import interrupt

@tool
def write_report(
    report_title: Annotated[str, "The title of the report"],
    report_content: Annotated[str, "The content of the report"],
    runtime: ToolRuntime
)->Command:
    """
    Write a report of the analysis performed.
    Interrupts the model to ask for approval before writing the report.
    """
    state = runtime.state

    # interrupt only if the writer is not editing an existing report
    if state["edit_instructions"] == "":

        # refine this message in frontend and simplify it here in backend (the user will not see this below)
        response = interrupt(f"The model has finished its analysis and wants to write a report. To continue, input 'yes'. To reject, input 'no'.")

        if response["type"] == "accept":
            pass
        elif response["type"] == "reject":
            return Command(goto="__end__")  # end flow - write report is the last thing after analysis completes
        else:
            raise ValueError(f"Invalid response type: {response['type']}")

    report_dict = {report_title: report_content}  # show this in frontend

    return Command(
        update = {
            "messages" : [ToolMessage(content="Report written successfully.", tool_call_id=runtime.tool_call_id)],
            "reports" : report_dict,
            "last_report_title" : report_title,
            "edit_instructions" : ""  # clear if there were any 
        }
    )

# probably should make a modify_report() tool that can be used to modify an existing report after it was approved. But maybe that can 
# be frontend only.
