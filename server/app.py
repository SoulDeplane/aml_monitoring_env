"""FastAPI application for the AML Monitoring environment."""

try:

    from openenv.core.env_server.http_server import create_app

    from openenv.core.env_server.mcp_types import CallToolAction, CallToolObservation

    from .environment import AMLMonitoringEnvironment

except ImportError:

    from openenv.core.env_server.http_server import create_app

    from openenv.core.env_server.mcp_types import CallToolAction, CallToolObservation

    from server.environment import AMLMonitoringEnvironment

app = create_app(

    AMLMonitoringEnvironment,

    CallToolAction,

    CallToolObservation,

    env_name="aml_monitoring_env",

)

def main():

    """Entry point for running the server directly."""

    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":

    main()

