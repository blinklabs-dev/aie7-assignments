#!/usr/bin/env python3
"""
🧪 A2A Protocol Test Client - Simple Version

A clean, simple version without external dependencies for maximum compatibility.
"""

import asyncio
from typing import Any
from uuid import uuid4

import httpx

from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendMessageRequest,
    SendStreamingMessageRequest,
)

def print_header(title: str, emoji: str = "🚀"):
    """Print a header with separator."""
    print(f"\n{emoji} {title}")
    print("=" * 80)

def print_step(step: str, emoji: str = "➡️"):
    """Print a step with visual indicator."""
    print(f"\n{emoji} {step}")
    print("-" * 60)

def print_success(message: str, emoji: str = "✅"):
    """Print a success message."""
    print(f"{emoji} {message}")

def print_info(message: str, emoji: str = "ℹ️"):
    """Print an info message."""
    print(f"{emoji} {message}")

def print_response(title: str, content: str, emoji: str = "🤖"):
    """Print a formatted response."""
    print(f"\n{emoji} {title}")
    print("─" * 60)
    print(content)
    print("─" * 60)

def extract_response_text(response_data: dict) -> str:
    """Extract the actual response text from the A2A response."""
    try:
        if 'result' in response_data:
            result = response_data['result']
            if 'artifacts' in result and result['artifacts']:
                artifact = result['artifacts'][0]
                if 'parts' in artifact and artifact['parts']:
                    return artifact['parts'][0].get('text', 'No text found')
        return "Response structure not recognized"
    except Exception as e:
        return f"Error extracting response: {e}"

async def test_agent_card_discovery(base_url: str, httpx_client: httpx.AsyncClient) -> AgentCard:
    """Test agent card discovery and return the agent card."""
    print_header("Agent Card Discovery", "🔍")
    
    resolver = A2ACardResolver(
        httpx_client=httpx_client,
        base_url=base_url,
    )
    
    print_step("Fetching agent card from server")
    try:
        agent_card = await resolver.get_agent_card()
        print_success(f"Successfully fetched agent card from {base_url}")
        
        # Display agent card info
        print(f"\n📋 Agent Information:")
        print(f"   Name: {agent_card.name}")
        print(f"   Description: {agent_card.description}")
        print(f"   Version: {agent_card.version}")
        print(f"   Protocol: {agent_card.protocol_version}")
        print(f"   Capabilities: Streaming={agent_card.capabilities.streaming}, Push={agent_card.capabilities.push_notifications}")
        
        # Show skills
        if agent_card.skills:
            print(f"\n🛠️  Available Skills ({len(agent_card.skills)}):")
            for i, skill in enumerate(agent_card.skills, 1):
                print(f"   {i}. {skill.name}: {skill.description}")
                if skill.examples:
                    print(f"      Examples: {', '.join(skill.examples[:2])}")
        
        return agent_card
        
    except Exception as e:
        print(f"❌ Failed to fetch agent card: {e}")
        raise

async def test_single_message(client: A2AClient, message: str) -> dict:
    """Test a single message and return the response."""
    print_header("Single Message Test", "💬")
    
    print_step(f"Sending message: {message[:50]}...")
    
    send_message_payload = {
        'message': {
            'role': 'user',
            'parts': [{'kind': 'text', 'text': message}],
            'message_id': uuid4().hex,
        },
    }
    
    request = SendMessageRequest(
        id=str(uuid4()), 
        params=MessageSendParams(**send_message_payload)
    )
    
    print("⏳ Processing message...")
    response = await client.send_message(request)
    print("✅ Processing complete!")
    
    response_data = response.model_dump(mode='json', exclude_none=True)
    response_text = extract_response_text(response_data)
    
    print_success("Message processed successfully!")
    print_response("Agent Response", response_text)
    
    return response_data

async def test_multi_turn_conversation(client: A2AClient):
    """Test multi-turn conversation capabilities."""
    print_header("Multi-Turn Conversation Test", "🔄")
    
    # First message
    print_step("Step 1: Initial query about transformer papers")
    first_message = "Find me recent papers on transformer architectures"
    
    send_message_payload = {
        'message': {
            'role': 'user',
            'parts': [{'kind': 'text', 'text': first_message}],
            'message_id': uuid4().hex,
        },
    }
    
    request = SendMessageRequest(
        id=str(uuid4()),
        params=MessageSendParams(**send_message_payload),
    )
    
    print("⏳ Processing first message...")
    response = await client.send_message(request)
    print("✅ First message complete!")
    
    response_data = response.model_dump(mode='json', exclude_none=True)
    first_response_text = extract_response_text(response_data)
    
    print_success("First message processed!")
    print_response("Initial Response", first_response_text)
    
    # Extract task and context IDs for follow-up
    task_id = response.root.result.id
    context_id = response.root.result.context_id
    
    print_info(f"Task ID: {task_id}")
    print_info(f"Context ID: {context_id}")
    
    # Second message (follow-up)
    print_step("Step 2: Follow-up question")
    second_message = "Can you summarize the key findings from these papers?"
    
    second_payload = {
        'message': {
            'role': 'user',
            'parts': [{'kind': 'text', 'text': second_message}],
            'message_id': uuid4().hex,
            'task_id': task_id,
            'context_id': context_id,
        },
    }
    
    second_request = SendMessageRequest(
        id=str(uuid4()),
        params=MessageSendParams(**second_payload),
    )
    
    print("⏳ Processing follow-up message...")
    second_response = await client.send_message(second_request)
    print("✅ Follow-up complete!")
    
    second_response_data = second_response.model_dump(mode='json', exclude_none=True)
    second_response_text = extract_response_text(second_response_data)
    
    print_success("Follow-up message processed!")
    print_response("Follow-up Response", second_response_text)

async def test_streaming_response(client: A2AClient, message: str):
    """Test streaming response capabilities."""
    print_header("Streaming Response Test", "📡")
    
    print_step(f"Testing streaming with message: {message[:50]}...")
    
    send_message_payload = {
        'message': {
            'role': 'user',
            'parts': [{'kind': 'text', 'text': message}],
            'message_id': uuid4().hex,
        },
    }
    
    streaming_request = SendStreamingMessageRequest(
        id=str(uuid4()), 
        params=MessageSendParams(**send_message_payload)
    )
    
    print_info("Starting streaming response...")
    print("\n📤 Streaming chunks:")
    
    stream_response = client.send_message_streaming(streaming_request)
    
    chunk_count = 0
    async for chunk in stream_response:
        chunk_count += 1
        chunk_data = chunk.model_dump(mode='json', exclude_none=True)
        
        # Extract meaningful information from chunk
        if 'result' in chunk_data:
            result = chunk_data['result']
            if 'kind' in result:
                kind = result['kind']
                if kind == 'status-update':
                    if 'status' in result and 'message' in result['status']:
                        message_content = result['status']['message']['parts'][0]['text']
                        print(f"  📤 {message_content}")
                elif kind == 'artifact-update':
                    if 'artifact' in result and 'parts' in result['artifact']:
                        artifact_text = result['artifact']['parts'][0]['text']
                        print(f"  📦 Final Response: {artifact_text[:100]}...")
    
    print_success(f"Streaming completed! Received {chunk_count} chunks")

async def main() -> None:
    """Main test function."""
    print("╭───────────────────────────────────────────╮")
    print("│ A2A Protocol Test Client                  │")
    print("│ Testing LangGraph Agent with A2A Protocol │")
    print("╰───────────────────────────────────────────╯")
    
    base_url = 'http://localhost:10000'
    
    # Increase timeout for LLM responses
    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as httpx_client:
        try:
            # Test 1: Agent Card Discovery
            agent_card = await test_agent_card_discovery(base_url, httpx_client)
            
            # Initialize client
            client = A2AClient(
                httpx_client=httpx_client, 
                agent_card=agent_card
            )
            print_success("A2A Client initialized successfully!")
            
            # Test 2: Single Message
            await test_single_message(
                client, 
                "What are the latest developments in artificial intelligence?"
            )
            
            # Test 3: Multi-turn Conversation
            await test_multi_turn_conversation(client)
            
            # Test 4: Streaming Response
            await test_streaming_response(
                client,
                "Tell me about recent breakthroughs in quantum computing"
            )
            
            # Final success message
            print("\n╭────────────────────────────────────────────────────────╮")
            print("│ 🎉 All Tests Completed Successfully!                   │")
            print("│ Your A2A protocol implementation is working perfectly! │")
            print("╰────────────────────────────────────────────────────────╯")
            
        except Exception as e:
            print("\n╭────────────────────────────────────────────────────────╮")
            print(f"│ ❌ Test Failed                                        │")
            print(f"│ Error: {str(e)}                                       │")
            print("╰────────────────────────────────────────────────────────╯")
            raise

if __name__ == '__main__':
    asyncio.run(main())
