"""Run development server."""
import uvicorn


def main():
    """Run uvicorn with reload."""
    uvicorn.run(
        "manning_patrol_backend:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()
