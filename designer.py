import streamlit as st
import yaml
import requests
import json
from main import Workflow # Import for type

st.title("Workflow Designer")

# Sidebar for node types
st.sidebar.header("Nodes")
node_types = ["event", "reconcile_orders", "restock_check", "decision", "alert"]
selected_type = st.sidebar.selectbox("Add Node", node_types)

# Canvas simulation (simple list-based; extend with JS for drag-drop)
if st.button("Add Node"):
    nodes = st.session_state.get("nodes", [])
    new_node = {
        "id": f"node_{len(nodes)}",
        "type": selected_type,
        "label": f"{selected_type} Node"
    }
    nodes.append(new_node)
    st.session_state["nodes"] = nodes
    st.rerun()

# Display nodes as "drag-drop" simulation (list with edit)
nodes = st.session_state.get("nodes", [])
for i, node in enumerate(nodes):
    col1, col2 = st.columns([3,1])
    with col1:
        st.write(f"{node['label']} ({node['type']})")
    with col2:
        if st.button("Edit", key=f"edit_{i}"):
            node["label"] = st.text_input("Label", node["label"], key=f"label_{i}")

# Edges (simple connect)
st.subheader("Edges")
edges = st.session_state.get("edges", [])
from_node = st.selectbox("From", [n["id"] for n in nodes] + [""])
condition = st.text_input("Condition (optional)")
if st.button("Add Edge"):
    if from_node and to_node:
        edges.append({"from": from_node, "to": to_node, "condition": condition or None})
        st.session_state["edges"] = edges
        st.rerun()

# Visualize (simple graph)
if st.button("Visualize"):
    st.graphviz_chart(
        """
            digraph G {
                start -> reconcile;
                reconcile -> restock;
                restock -> alert [label="low"];
                restock -> end [label="ok"];
            }
        """
    ) # Placeholder; use networkx for dynamix

# Export/Import
wf_data = {
    "nodes": nodes,
    "edges": edges
}
if st.button("Export JSON"):
    st.download_button("Download", json.dumps(wf_data), "workflow.json")

uploaded = st.file_uploader("Import YAML/JSON")
if uploaded:
    content = yaml.safe_load(uploaded) if uploaded.name.endswitch('.yaml') else json.load(uploaded)
    st.session_state["nodes"] = content["nodes"]
    st.session_state["edges"] = content["edges"]
    st.rerun()

# Save to API
if st.button("Save Workflow"):
    wf = Workflow(id="", nodes=nodes, edges=edges)
    response = requests.post("http://localhost:8000/workflows", json=wf.dict())
    st.success(f"Saved! ID: {response.json()['id']}")