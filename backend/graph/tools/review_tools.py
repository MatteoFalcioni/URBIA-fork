from typing_extensions import Annotated
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import HumanMessage, ToolMessage
from langgraph.types import Command

@tool
async def approve_analysis_tool(
    runtime: ToolRuntime
) -> Command:   
    """
    Use this to approve the analysis.

    """
    print(f"***approving analysis in approve_analysis_tool")
    return Command(
        update={
            "analysis_status": "approved",
            "analysis_comments" : "", # reset any analysis comments (they are for rejected analyses)
            "messages" : [ToolMessage(content=f"Analysis approved from the reviewer.", tool_call_id=runtime.tool_call_id)],
        }
    )

@tool
async def reject_analysis_tool(
    comments: Annotated[str, "Comments for the analyst to improve the analysis"],
    runtime: ToolRuntime
) -> Command:   
    """
    Use this to reject the analysis, with constructive criticism for the analyst to improve the analysis.
    Arguments:
        comments: Constructive criticism for the analyst to improve the analysis.
    """
    print(f"***rejecting analysis in reject_analysis_tool: {comments}")
    return Command(
        update={
            "analysis_status": "rejected",
            "analysis_comments": comments,
            "reroute_count" : 1,
            "messages" : [ToolMessage(content=f"Analysis rejected by reviewer, with the following comments for the analyst:\n {comments}", tool_call_id=runtime.tool_call_id)],
        }
    )

@tool 
async def update_completeness_score(grade: Annotated[int, "The grade of the completeness score"], runtime: ToolRuntime) -> Command:
    """
    Use this to update the completeness score.
    Arguments:
        grade: The grade of the completeness score
    """
    print(f"***updating completeness score in update_completeness_score: {grade}")
    return Command(update={
        "messages" : [ToolMessage(content=f"Completeness score updated to: {grade}", tool_call_id=runtime.tool_call_id)],
        "completeness_score": grade
    })

@tool 
async def update_correctness_score(grade: Annotated[int, "The grade of the correctness score"], runtime: ToolRuntime) -> Command:
    """
    Use this to update the correctness score.
    Arguments:
        grade: The grade of the correctness score
    """
    print(f"***updating correctness score in update_correctness_score: {grade}")
    return Command(update={
        "messages" : [ToolMessage(content=f"Correctness score updated to: {grade}", tool_call_id=runtime.tool_call_id)],
        "correctness_score": grade
    })

@tool 
async def update_reliability_score(score: Annotated[int, "The score of the reliability score"], runtime: ToolRuntime) -> Command:
    """
    Use this to update the reliability score.
    Arguments:
        score: The score of the reliability score
    Returns:
        the normalized reliability score between 0 and 10
    """
    sources_list = runtime.state['sources']
    
    # normalize the score between 0 and 10
    # get the number of sources: thats the max of the grade (+1 for every right, -1 for every wrong -> ex: 7 sources, grade in [-7,+7])
    n_sources = len(sources_list)   # it's max grade ossible (if 7 sources, max grade is 7)
    # 10 : n_sources = normalized_score : score -> normalized_score = score * (10 / n_sources)
    # also handle errors in division by 0
    if n_sources != 0:
        normalized_score = score * (10 / n_sources)    
    # we choose to not compute it and leave it out of the average in the final grade if there are no sources: 
    # it could be that the reviewer was assigned a review for a simple analysis that the data analyst performed without using datasets
    else: 
        return Command(
            update={
                "messages" : [ToolMessage(content=f"There are no sources listed, so the reliability score cannot be computed.", tool_call_id=runtime.tool_call_id)]
            }
        )

    print(f"***updating reliability score in update_reliability_score: {score}")
    return Command(update={
        "messages" : [ToolMessage(content=f"Reliability score updated to: {normalized_score}", tool_call_id=runtime.tool_call_id)],
        "reliability_score": normalized_score
    })

@tool
async def complete_review_tool(runtime: ToolRuntime) -> Command:
    """
    Use this to complete the review.
    Returns:
        the final score between 0 and 10
    """
    completeness_score = runtime.state['completeness_score']
    reliability_score = runtime.state.get('reliability_score', None)
    correctness_score = runtime.state['correctness_score']

    if reliability_score is not None:
        final_score = (completeness_score + reliability_score + correctness_score) / 3
        note_msg = []
    else: 
        final_score = (completeness_score + correctness_score) / 2
        note_msg = [HumanMessage(content="The reliability score was not found - this means the data analyst did not present any sources. If the analysis did not use any datasets, this is fine. Otherwise, this is an error.")]

    print(f"***completing review in complete_review_tool: final score is {final_score}")
    return Command(update={
        "messages" : [ToolMessage(content=f"Review completed: final score is {final_score}", tool_call_id=runtime.tool_call_id)] + note_msg,
        "final_score" : final_score
    })