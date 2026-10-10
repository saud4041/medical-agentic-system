import os
import sys

project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.graph import medical_agent_graph


def generate_and_save_graph():
    """Renders the LangGraph multi-agent cognitive architecture to the 'gen/' directory."""
    target_dir = "gen"
    target_file = os.path.join(target_dir, "medical_agent_graph.png")

    # Ensure the target generation directory exists
    os.makedirs(target_dir, exist_ok=True)

    print("🎨 Initializing LangGraph Mermaid rendering engine pipeline...")

    try:
        # Generate raw binary image bytes using LangGraph's visualizer compiler
        png_bytes = medical_agent_graph.get_graph().draw_mermaid_png()

        with open(target_file, "wb") as f:
            f.write(png_bytes)

        print(
            f"✅ Success! Architectural flowchart compiled and saved to: {target_file}"
        )

    except Exception as e:
        print(f"❌ Standard binary rendering failed: {str(e)}")
        print("\n💡 Alternative Text Blueprint Representation (ASCII Flowchart):")
        try:
            medical_agent_graph.get_graph().print_ascii()
        except Exception:
            pass


if __name__ == "__main__":
    generate_and_save_graph()
