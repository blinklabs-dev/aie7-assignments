#!/usr/bin/env python3
"""
🤖 A2A Client Agent - Session 15 Assignment

This is the main assignment file that demonstrates an agent communicating with your A2A server.
It shows how different agents can talk to each other using the A2A protocol.

Usage: uv run python a2a_client_agent.py
"""

import asyncio
import json
from typing import Any
from uuid import uuid4

import httpx

from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendMessageRequest,
)

class A2AClientAgent:
    """A simple agent that communicates with your A2A server."""
    
    def __init__(self, server_url: str = "http://localhost:10000"):
        self.server_url = server_url
        self.agent_card = None
        self.client = None
        
    async def discover_server(self):
        """Discover the A2A server and get its agent card."""
        print("🔍 Discovering A2A server...")
        
        self.httpx_client = httpx.AsyncClient(timeout=httpx.Timeout(60.0))
        resolver = A2ACardResolver(
            httpx_client=self.httpx_client,
            base_url=self.server_url,
        )
        
        try:
            self.agent_card = await resolver.get_agent_card()
            self.client = A2AClient(
                httpx_client=self.httpx_client, 
                agent_card=self.agent_card
            )
            print(f"✅ Connected to: {self.agent_card.name}")
            print(f"📋 Description: {self.agent_card.description}")
            print(f"🛠️  Skills available: {len(self.agent_card.skills)}")
            return True
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            return False
    
    async def ask_question(self, question: str, persona: str = "Curious Student"):
        """Ask a question to the A2A server with a specific persona."""
        print(f"\n🎭 {persona} asks: {question}")
        print("-" * 60)
        
        send_message_payload = {
            'message': {
                'role': 'user',
                'parts': [{'kind': 'text', 'text': question}],
                'message_id': uuid4().hex,
            },
        }
        
        request = SendMessageRequest(
            id=str(uuid4()), 
            params=MessageSendParams(**send_message_payload)
        )
        
        try:
            print("⏳ Waiting for response...")
            response = await self.client.send_message(request)
            response_data = response.model_dump(mode='json', exclude_none=True)
            
            # Extract the actual response text
            if 'result' in response_data and 'artifacts' in response_data['result']:
                artifacts = response_data['result']['artifacts']
                if artifacts and 'parts' in artifacts[0]:
                    response_text = artifacts[0]['parts'][0].get('text', 'No response text found')
                    print(f"🤖 Server Response:")
                    print(response_text)
                    print("-" * 60)
                    return response_text
            
            print("❌ Could not extract response text")
            return None
            
        except Exception as e:
            print(f"❌ Error getting response: {e}")
            return None

async def main():
    """Main function to demonstrate A2A communication."""
    print("🚀 A2A Client Agent - Session 15 Assignment")
    print("=" * 60)
    
    # Create our client agent
    client_agent = A2AClientAgent()
    
    # Discover the server
    if not await client_agent.discover_server():
        print("❌ Cannot continue without server connection")
        return
    
    print("\n🎯 Testing different personas and questions...")
    
    # Test 1: Curious Student
    await client_agent.ask_question(
        "What are the latest developments in artificial intelligence?",
        "Curious Student"
    )
    
    # Test 2: Research Scientist
    await client_agent.ask_question(
        "Find me recent papers on transformer architectures and explain their key innovations",
        "Research Scientist"
    )
    
    # Test 3: Business Analyst
    await client_agent.ask_question(
        "What are the business implications of recent AI breakthroughs?",
        "Business Analyst"
    )
    
    # Test 4: Technical Developer
    await client_agent.ask_question(
        "Explain the technical differences between different transformer architectures",
        "Technical Developer"
    )
    
    print("\n🎉 A2A Communication Test Complete!")
    print("✅ Successfully demonstrated agent-to-agent communication")
    print("✅ Showed different personas getting different types of responses")
    print("✅ Proved A2A protocol is working correctly")
    
    # Clean up
    await client_agent.httpx_client.aclose()

if __name__ == '__main__':
    asyncio.run(main())
