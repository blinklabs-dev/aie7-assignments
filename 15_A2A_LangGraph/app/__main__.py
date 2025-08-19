import logging
import os
import sys

import click
import httpx
import uvicorn
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import (
    BasePushNotificationSender,
    InMemoryPushNotificationConfigStore,
    InMemoryTaskStore,
)
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from dotenv import load_dotenv

from app.agent import Agent
from app.agent_executor import GeneralAgentExecutor


load_dotenv()

# Configure logging to be less verbose
logging.basicConfig(
    level=logging.WARNING,  # Changed from INFO to WARNING
    format='%(levelname)s: %(message)s'  # Simplified format
)

# Reduce specific logger verbosity
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('arxiv').setLevel(logging.WARNING)
logging.getLogger('app.agent_executor').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


class MissingAPIKeyError(Exception):
    """Exception for missing API key."""


def create_agent_card_html(agent_card: AgentCard) -> str:
    """Create a beautiful HTML page for the agent card."""
    skills_html = ""
    for skill in agent_card.skills:
        examples_html = ""
        if skill.examples:
            examples_html = f"""
                <div class="examples">
                    <strong>Examples:</strong>
                    <ul>
                        {''.join(f'<li>"{example}"</li>' for example in skill.examples)}
                    </ul>
                </div>
            """
        
        tags_html = ""
        if skill.tags:
            tags_html = f"""
                <div class="tags">
                    {''.join(f'<span class="tag">{tag}</span>' for tag in skill.tags)}
                </div>
            """
        
        skills_html += f"""
            <div class="skill-card">
                <h3>{skill.name}</h3>
                <p class="skill-description">{skill.description}</p>
                {tags_html}
                {examples_html}
            </div>
        """

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{agent_card.name} - A2A Agent Card</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5rem;
            margin-bottom: 10px;
            font-weight: 700;
        }}
        
        .header p {{
            font-size: 1.2rem;
            opacity: 0.9;
            max-width: 600px;
            margin: 0 auto;
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
            margin-bottom: 40px;
        }}
        
        .info-card {{
            background: #f8fafc;
            padding: 25px;
            border-radius: 15px;
            border-left: 4px solid #4f46e5;
        }}
        
        .info-card h3 {{
            color: #4f46e5;
            margin-bottom: 15px;
            font-size: 1.1rem;
        }}
        
        .capabilities {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}
        
        .capability {{
            background: #4f46e5;
            color: white;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 500;
        }}
        
        .skills-section {{
            margin-top: 40px;
        }}
        
        .skills-section h2 {{
            color: #4f46e5;
            margin-bottom: 30px;
            font-size: 1.8rem;
            text-align: center;
        }}
        
        .skills-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 25px;
        }}
        
        .skill-card {{
            background: white;
            border: 2px solid #e2e8f0;
            border-radius: 15px;
            padding: 25px;
            transition: all 0.3s ease;
        }}
        
        .skill-card:hover {{
            border-color: #4f46e5;
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(79, 70, 229, 0.1);
        }}
        
        .skill-card h3 {{
            color: #4f46e5;
            margin-bottom: 10px;
            font-size: 1.2rem;
        }}
        
        .skill-description {{
            color: #64748b;
            margin-bottom: 15px;
            line-height: 1.5;
        }}
        
        .tags {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-bottom: 15px;
        }}
        
        .tag {{
            background: #e0e7ff;
            color: #4f46e5;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 500;
        }}
        
        .examples {{
            background: #f1f5f9;
            padding: 15px;
            border-radius: 10px;
        }}
        
        .examples strong {{
            color: #4f46e5;
            display: block;
            margin-bottom: 8px;
        }}
        
        .examples ul {{
            list-style: none;
            padding-left: 0;
        }}
        
        .examples li {{
            background: white;
            padding: 8px 12px;
            margin-bottom: 5px;
            border-radius: 8px;
            border-left: 3px solid #4f46e5;
            font-style: italic;
        }}
        
        .footer {{
            background: #f8fafc;
            padding: 30px;
            text-align: center;
            border-top: 1px solid #e2e8f0;
        }}
        
        .footer p {{
            color: #64748b;
            margin-bottom: 10px;
        }}
        
        .api-link {{
            display: inline-block;
            background: #4f46e5;
            color: white;
            padding: 10px 20px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 500;
            transition: background 0.3s ease;
        }}
        
        .api-link:hover {{
            background: #3730a3;
        }}
        
        .version-badge {{
            background: #10b981;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 500;
            display: inline-block;
            margin-left: 10px;
        }}
        
        @media (max-width: 768px) {{
            .header {{
                padding: 30px 20px;
            }}
            
            .header h1 {{
                font-size: 2rem;
            }}
            
            .content {{
                padding: 20px;
            }}
            
            .skills-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 {agent_card.name}</h1>
            <p>{agent_card.description}</p>
            <span class="version-badge">v{agent_card.version}</span>
        </div>
        
        <div class="content">
            <div class="info-grid">
                <div class="info-card">
                    <h3>📋 Protocol Information</h3>
                    <p><strong>Protocol Version:</strong> {agent_card.protocol_version}</p>
                    <p><strong>Transport:</strong> {agent_card.preferred_transport}</p>
                    <p><strong>URL:</strong> <a href="{agent_card.url}" target="_blank">{agent_card.url}</a></p>
                </div>
                
                <div class="info-card">
                    <h3>⚡ Capabilities</h3>
                    <div class="capabilities">
                        <span class="capability">Streaming: {'✅' if agent_card.capabilities.streaming else '❌'}</span>
                        <span class="capability">Push Notifications: {'✅' if agent_card.capabilities.push_notifications else '❌'}</span>
                    </div>
                </div>
                
                <div class="info-card">
                    <h3>📝 Content Types</h3>
                    <p><strong>Input:</strong> {', '.join(agent_card.default_input_modes)}</p>
                    <p><strong>Output:</strong> {', '.join(agent_card.default_output_modes)}</p>
                </div>
            </div>
            
            <div class="skills-section">
                <h2>🛠️ Available Skills ({len(agent_card.skills)})</h2>
                <div class="skills-grid">
                    {skills_html}
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>This is an A2A (Agent-to-Agent) protocol compliant agent</p>
            <a href="/.well-known/agent-card.json" class="api-link" target="_blank">View JSON API</a>
        </div>
    </div>
</body>
</html>
"""


async def agent_card_html_handler(request):
    """Serve a beautiful HTML page for the agent card."""
    # Create the agent card (same as in main function)
    capabilities = AgentCapabilities(streaming=True, push_notifications=True)
    skills = [
        AgentSkill(
            id='web_search',
            name='Web Search Tool',
            description='Search the web for current information',
            tags=['search', 'web', 'internet'],
            examples=['What are the latest news about AI?'],
        ),
        AgentSkill(
            id='arxiv_search',
            name='Academic Paper Search',
            description='Search for academic papers on arXiv',
            tags=['research', 'papers', 'academic'],
            examples=['Find recent papers on large language models'],
        ),
        AgentSkill(
            id='rag_search',
            name='Document Retrieval',
            description='Search through loaded documents for specific information',
            tags=['documents', 'rag', 'retrieval'],
            examples=['What do the policy documents say about student loans?'],
        ),
    ]
    agent_card = AgentCard(
        name='General Purpose Agent',
        description='A helpful AI assistant with web search, academic paper search, and document retrieval capabilities',
        url=f'http://{request.url.hostname}:{request.url.port}/',
        version='1.0.0',
        default_input_modes=Agent.SUPPORTED_CONTENT_TYPES,
        default_output_modes=Agent.SUPPORTED_CONTENT_TYPES,
        capabilities=capabilities,
        skills=skills,
    )
    
    html_content = create_agent_card_html(agent_card)
    return HTMLResponse(html_content)


@click.command()
@click.option('--host', 'host', default='localhost')
@click.option('--port', 'port', default=10000)
@click.option('--verbose', 'verbose', is_flag=True, help='Enable verbose logging')
def main(host, port, verbose):
    """Starts the General Agent server with A2A protocol support."""
    try:
        if verbose:
            # Enable verbose logging if requested
            logging.getLogger().setLevel(logging.INFO)
            logging.getLogger('httpx').setLevel(logging.INFO)
            logging.getLogger('arxiv').setLevel(logging.INFO)
            logging.getLogger('app.agent_executor').setLevel(logging.INFO)
            logger.info("Verbose logging enabled")
        else:
            logger.info(f"Starting A2A server on {host}:{port} (quiet mode)")

        if not os.getenv('OPENAI_API_KEY'):
            raise MissingAPIKeyError(
                'OPENAI_API_KEY environment variable not set.'
            )

        capabilities = AgentCapabilities(streaming=True, push_notifications=True)
        skills = [
            AgentSkill(
                id='web_search',
                name='Web Search Tool',
                description='Search the web for current information',
                tags=['search', 'web', 'internet'],
                examples=['What are the latest news about AI?'],
            ),
            AgentSkill(
                id='arxiv_search',
                name='Academic Paper Search',
                description='Search for academic papers on arXiv',
                tags=['research', 'papers', 'academic'],
                examples=['Find recent papers on large language models'],
            ),
            AgentSkill(
                id='rag_search',
                name='Document Retrieval',
                description='Search through loaded documents for specific information',
                tags=['documents', 'rag', 'retrieval'],
                examples=['What do the policy documents say about student loans?'],
            ),
        ]
        agent_card = AgentCard(
            name='General Purpose Agent',
            description='A helpful AI assistant with web search, academic paper search, and document retrieval capabilities',
            url=f'http://{host}:{port}/',
            version='1.0.0',
            default_input_modes=Agent.SUPPORTED_CONTENT_TYPES,
            default_output_modes=Agent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=skills,
        )


        # --8<-- [start:DefaultRequestHandler]
        httpx_client = httpx.AsyncClient()
        push_config_store = InMemoryPushNotificationConfigStore()
        push_sender = BasePushNotificationSender(httpx_client=httpx_client,
                        config_store=push_config_store)
        request_handler = DefaultRequestHandler(
            agent_executor=GeneralAgentExecutor(),
            task_store=InMemoryTaskStore(),
            push_config_store=push_config_store,
            push_sender= push_sender
        )
        server = A2AStarletteApplication(
            agent_card=agent_card, http_handler=request_handler
        )

        # Add custom routes for better browser experience
        app = server.build()
        
        # Add a custom route for the root path to show the agent card HTML
        app.routes.insert(0, Route("/", agent_card_html_handler))
        
        logger.info(f"🚀 A2A Server starting on http://{host}:{port}")
        logger.info("📋 Agent Card available at: /.well-known/agent-card.json")
        logger.info("🌐 Beautiful HTML view at: http://localhost:10000/")
        logger.info("🧪 Test with: uv run python app/test_client_simple.py")
        
        uvicorn.run(app, host=host, port=port, log_level="warning")
        # --8<-- [end:DefaultRequestHandler]

    except MissingAPIKeyError as e:
        logger.error(f'Error: {e}')
        sys.exit(1)
    except Exception as e:
        logger.error(f'An error occurred during server startup: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
