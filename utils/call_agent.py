from google.genai import types  # For creating message Content/Parts


async def call_agent_async(query: str, runner, user_id, session_id):
    """Sends a query to the agent and prints the final response."""
    print(f"\n>>> User Query for user {user_id}, session {session_id}: {query}")

    # Prepare the user's message in ADK format
    content = types.Content(role="user", parts=[types.Part(text=query)])

    final_response_text = "Agent did not produce a final response."  # Default

    # Key Concept: run_async executes the agent logic and yields Events.
    # We iterate through events to find the final answer.
    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=content
    ):
        # You can uncomment the line below to see *all* events during execution
        # print(f"  [Event] Author: {event.author}, Type: {type(event).__name__}, Final: {event.is_final_response()}, Content: {event.content}")

        # Key Concept: is_final_response() marks the concluding message for the turn.
        if event.is_final_response():
            if event.content and event.content.parts:
                for part in event.content.parts:
                    print("DEBUG part.text:", repr(part.text))
                # Assuming text response in the first part
                final_response_text = event.content.parts[0].text
            elif (
                event.actions and event.actions.escalate
            ):  # Handle potential errors/escalations
                final_response_text = (
                    f"Agent escalated: {event.error_message or 'No specific message.'}"
                )
            # Add more checks here if needed (e.g., specific error codes)
            break  # Stop processing events once the final response is found

    print(f"<<< Agent Response: {final_response_text}")
    return final_response_text


async def stream_agent_responses(
    query: str, runner, user_id, session_id, use_function_map=None
):
    print(f"\n>>> User Query for user {user_id}, session {session_id}: {query}")
    user_content = types.Content(role="user", parts=[types.Part(text=query)])
    event_yielded_content = False

    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=user_content
    ):
        if hasattr(event, "content") and event.content:
            if event.content.parts:
                for i, part_debug in enumerate(event.content.parts):
                    part_info = []
                    if part_debug.text:
                        part_info.append("Has Text")
                    if (
                        hasattr(part_debug, "function_call")
                        and part_debug.function_call
                    ):
                        part_info.append(
                            f"Has FunctionCall (name: {part_debug.function_call.name})"
                        )

        if hasattr(event, "actions") and event.actions:
            action_debug_info = []
            if hasattr(event.actions, "escalate"):
                action_debug_info.append(
                    f"Escalate={'Set' if event.actions.escalate else 'None'}"
                )
            else:
                action_debug_info.append("Escalate=NotPresent")
            if hasattr(event.actions, "tool_code"):
                action_debug_info.append(
                    f"ToolCode={'Set' if event.actions.tool_code else 'None'}"
                )
            else:
                action_debug_info.append("ToolCode=NotPresent")

        event_yielded_content = False

        if event.content and event.content.role == "model" and event.content.parts:
            for part in event.content.parts:
                message_to_yield = None

                if part.text:
                    message_to_yield = part.text
                    print(
                        f'<<< Agent text part (yielding): "{message_to_yield[:100]}..."'
                    )

                elif hasattr(part, "function_call") and part.function_call:
                    func_name = part.function_call.name

                    if use_function_map and func_name in use_function_map:
                        message_to_yield = "（" + use_function_map[func_name] + "）"
                        print(
                            f"<<< Agent function_call received: {func_name} — yielding mapped string only (no execution)."
                        )
                        print(
                            f"⚠️ [Warning Suppressed] Non-text part detected (function_call), but converted to message: '{message_to_yield}'"
                        )
                    else:
                        message_to_yield = f"⚠️ [Unknown FunctionCall]: {func_name}"
                        print(
                            f"⚠️ [Unhandled FunctionCall] {func_name} not in use_function_map — yielded fallback message."
                        )

                if message_to_yield:
                    yield message_to_yield
                    event_yielded_content = True

        if event.is_final_response():
            print(f"<<< Final event received (ID: {getattr(event, 'id', 'N/A')}).")

            if (
                event.actions
                and hasattr(event.actions, "escalate")
                and event.actions.escalate
            ):
                escalation_message = f"⚠️ *Agent escalated*: {event.error_message or 'No specific message.'}"
                print(f"<<< Agent escalated (yielding message): {escalation_message}")
                yield escalation_message

            if not event_yielded_content:
                print("<<< Final event did not yield new textual/tool content itself.")

            return

    print("<<< Stream ended unexpectedly without a designated final response event.")
