#!/usr/bin/env python3
"""
Streamlit UI for Conversation Evaluation Benchmark
"""

import streamlit as st
import pandas as pd
import json
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from facet_manager import FacetManager
from conversation_evaluator import ConversationEvaluator, ConversationTurn

# ==================== Page Configuration ====================

st.set_page_config(
    page_title="Conversation Evaluation Benchmark",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== Styling ====================

st.markdown("""
<style>
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
    .evaluation-card {
        border-left: 4px solid #1f77b4;
        padding: 10px;
        margin: 5px 0;
        background-color: #f9f9f9;
    }
</style>
""", unsafe_allow_html=True)

# ==================== Session State ====================

@st.cache_resource
def load_facet_manager():
    """Load facet manager"""
    # Try multiple locations
    facets_file = Path("conversation_evaluation_output/facets/facets_processed.json")
    if not facets_file.exists():
        facets_file = Path("data/facets_processed.json")
    if facets_file.exists():
        return FacetManager(str(facets_file))
    else:
        st.error("Facets file not found. Please run the pipeline first.")
        st.stop()

@st.cache_resource
def load_evaluator():
    """Load evaluator"""
    manager = load_facet_manager()
    return ConversationEvaluator(facet_manager=manager)

# ==================== Sidebar ====================

st.sidebar.title("🎯 Navigation")

page = st.sidebar.radio("Select Page", [
    "Home",
    "Evaluate Conversation",
    "Facet Explorer",
    "View Results",
    "About"
])

# ==================== Home Page ====================

def show_home():
    st.title("🎯 Conversation Evaluation Benchmark")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("""
        ## Welcome to the Conversation Evaluation Benchmark
        
        This system evaluates conversations on **300+ distinct facets** covering:
        - 📝 **Linguistic Quality** (grammar, clarity, vocabulary)
        - 💭 **Pragmatics** (relevance, context, appropriateness)
        - 🛡️ **Safety** (harmful content, bias, ethics)
        - 😊 **Emotion** (empathy, sentiment, engagement)
        
        ### Key Features
        - ✅ **Scalable Architecture**: Supports 5000+ facets without redesign
        - ✅ **Confidence Scores**: Get confidence intervals with each evaluation
        - ✅ **Production-Ready**: Docker-deployable backend
        - ✅ **Open-Weights LLMs**: Compatible with Llama 3, Qwen2, Mixtral
        """)
    
    with col2:
        st.image("https://via.placeholder.com/300x200?text=Conversation+Evaluation", use_column_width=True)
    
    # Statistics
    st.markdown("---")
    st.subheader("📊 System Statistics")
    
    manager = load_facet_manager()
    stats = manager.get_facet_statistics()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Facets", f"{stats['total_facets']}")
    with col2:
        st.metric("Categories", f"{stats['total_categories']}")
    with col3:
        st.metric("High Priority", len(manager.get_facets_by_priority("high")))
    with col4:
        st.metric("Evaluation Methods", "3+")
    
    # Sample Conversations
    st.markdown("---")
    st.subheader("📋 Quick Demo")
    
    if st.button("Load Sample Conversations"):
        conversations_file = Path("conversation_evaluation_output/conversations/sample_conversations.json")
        if not conversations_file.exists():
            conversations_file = Path("data/conversations/sample_conversations.json")
        if conversations_file.exists():
            with open(conversations_file) as f:
                data = json.load(f)
                st.success(f"Loaded {data['total_conversations']} sample conversations")
                st.json(data['conversations'][0])

# ==================== Evaluate Conversation Page ====================

def show_evaluate():
    st.title("💬 Evaluate Conversation")
    
    st.markdown("""
    Enter a conversation turn by turn and get instant evaluation across multiple facets.
    """)
    
    manager = load_facet_manager()
    evaluator = load_evaluator()
    
    # Input type selection
    input_type = st.radio("Input Type", ["Manual Entry", "Sample Conversation", "JSON Upload"])
    
    if input_type == "Manual Entry":
        st.subheader("Enter Conversation Turns")
        
        turns = []
        num_turns = st.number_input("Number of turns", min_value=1, max_value=10, value=2)
        
        for i in range(num_turns):
            with st.expander(f"Turn {i+1}"):
                speaker = st.selectbox(
                    f"Speaker {i+1}",
                    ["user", "assistant"],
                    key=f"speaker_{i}"
                )
                content = st.text_area(
                    f"Content {i+1}",
                    key=f"content_{i}",
                    height=100
                )
                if content:
                    turns.append((speaker, content))
    
    elif input_type == "Sample Conversation":
        conversations_file = Path("conversation_evaluation_output/conversations/sample_conversations.json")
        if not conversations_file.exists():
            conversations_file = Path("data/conversations/sample_conversations.json")
        if conversations_file.exists():
            with open(conversations_file) as f:
                data = json.load(f)
                conversations = data['conversations']
            
            selected_conv = st.selectbox(
                "Select a sample conversation",
                range(len(conversations)),
                format_func=lambda x: f"{conversations[x]['description']} ({conversations[x]['conversation_id']})"
            )
            
            conv = conversations[selected_conv]
            turns = [(t["speaker"], t["content"]) for t in conv["turns"]]
            
            st.info(f"Category: {conv['category']} | Quality: {conv['quality_level']}")
    
    else:  # JSON Upload
        uploaded_file = st.file_uploader("Upload JSON file", type="json")
        if uploaded_file:
            data = json.load(uploaded_file)
            if "turns" in data:
                turns = [(t["speaker"], t["content"]) for t in data["turns"]]
            else:
                st.error("JSON must contain 'turns' field")
                turns = []
    
    # Evaluation options
    st.subheader("Evaluation Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        facet_category = st.selectbox(
            "Facet Category",
            ["All"] + list(manager.facets_by_category.keys())
        )
    
    with col2:
        batch_eval = st.checkbox("Batch Evaluation", value=True)
    
    # Run evaluation
    if st.button("🚀 Evaluate Conversation", type="primary"):
        if not turns:
            st.error("Please enter at least one conversation turn")
        else:
            with st.spinner("Evaluating..."):
                try:
                    conversation = evaluator.create_conversation(turns)
                    evaluated = evaluator.evaluate_conversation(conversation)
                    
                    # Display results
                    st.success("✅ Evaluation Complete")
                    
                    # Overall Score
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Score", f"{evaluated.total_score:.2f}/5")
                    with col2:
                        st.metric("Avg Confidence", f"{evaluated.get_average_confidence():.2%}")
                    with col3:
                        st.metric("Facets Evaluated", evaluated.facets_evaluated)
                    
                    # Detailed Results
                    st.subheader("📊 Detailed Evaluation")
                    
                    for turn_eval in evaluated.turn_evaluations:
                        with st.expander(f"Turn: {turn_eval.speaker.upper()} - Score: {turn_eval.overall_quality:.2f}/5"):
                            # Display turn content
                            st.markdown(f"**Content**: {turn_eval.content[:200]}...")
                            
                            # Create DataFrame for facet scores
                            scores_data = {
                                "Facet": [s.facet_name for s in turn_eval.facet_scores],
                                "Score": [s.score for s in turn_eval.facet_scores],
                                "Confidence": [f"{s.confidence:.2%}" for s in turn_eval.facet_scores],
                                "Reasoning": [s.reasoning for s in turn_eval.facet_scores]
                            }
                            
                            df = pd.DataFrame(scores_data)
                            st.dataframe(df, use_container_width=True)
                            
                            # Visualization
                            if turn_eval.facet_scores:
                                scores_dict = {s.facet_name: s.score for s in turn_eval.facet_scores}
                                fig = px.bar(
                                    x=list(scores_dict.keys())[:10],
                                    y=list(scores_dict.values())[:10],
                                    title="Top 10 Facet Scores",
                                    labels={"x": "Facet", "y": "Score"}
                                )
                                st.plotly_chart(fig, use_container_width=True)
                    
                    # Export option
                    st.subheader("💾 Export Results")
                    export_format = st.radio("Format", ["JSON", "CSV"])
                    
                    if st.button("Download"):
                        if export_format == "JSON":
                            json_str = json.dumps(evaluated.to_dict(), indent=2, default=str)
                            st.download_button(
                                "Download JSON",
                                json_str,
                                f"evaluation_{evaluated.conversation_id}.json",
                                "application/json"
                            )
                        else:
                            # Create CSV from facet scores
                            all_scores = []
                            for turn_eval in evaluated.turn_evaluations:
                                for score in turn_eval.facet_scores:
                                    all_scores.append({
                                        "Turn": turn_eval.turn_id,
                                        "Speaker": turn_eval.speaker,
                                        "Facet": score.facet_name,
                                        "Score": score.score,
                                        "Confidence": score.confidence
                                    })
                            
                            df = pd.DataFrame(all_scores)
                            csv = df.to_csv(index=False)
                            st.download_button(
                                "Download CSV",
                                csv,
                                f"evaluation_{evaluated.conversation_id}.csv",
                                "text/csv"
                            )
                
                except Exception as e:
                    st.error(f"Evaluation failed: {e}")

# ==================== Facet Explorer Page ====================

def show_facet_explorer():
    st.title("🔍 Facet Explorer")
    
    manager = load_facet_manager()
    stats = manager.get_facet_statistics()
    
    # Display category distribution
    st.subheader("📊 Category Distribution")
    
    categories = stats['category_distribution']
    fig = px.pie(
        values=list(categories.values()),
        names=list(categories.keys()),
        title="Facets by Category"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Facet listing
    st.subheader("📋 All Facets")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_category = st.selectbox("Category", ["All"] + list(manager.facets_by_category.keys()))
    with col2:
        selected_priority = st.selectbox("Priority", ["All", "low", "medium", "high"])
    with col3:
        search_term = st.text_input("Search", "")
    
    # Get filtered facets
    if selected_category == "All":
        facets = list(manager.facets.values())
    else:
        facets = manager.get_facets_by_category(selected_category)
    
    if selected_priority != "All":
        facets = [f for f in facets if f.priority == selected_priority]
    
    if search_term:
        facets = [f for f in facets if search_term.lower() in f.name.lower()]
    
    # Display facets as table
    facet_data = [
        {
            "ID": f.id,
            "Name": f.name,
            "Category": f.category,
            "Priority": f.priority,
            "Difficulty": f.evaluation_difficulty
        }
        for f in facets
    ]
    
    df = pd.DataFrame(facet_data)
    st.dataframe(df, use_container_width=True, height=400)
    
    st.info(f"Showing {len(facets)} facets out of {manager.total_facets} total")

# ==================== View Results Page ====================

def show_results():
    st.title("📈 View Results")
    
    st.markdown("""
    View previous evaluation results and generate reports.
    """)
    
    evaluations_dir = Path("data/evaluations")
    
    if evaluations_dir.exists():
        eval_files = list(evaluations_dir.glob("*_evaluation.json"))
        
        if eval_files:
            selected_file = st.selectbox(
                "Select Evaluation",
                eval_files,
                format_func=lambda x: x.stem
            )
            
            with open(selected_file) as f:
                eval_data = json.load(f)
            
            # Display evaluation
            st.json(eval_data)
        else:
            st.info("No evaluation results found. Run the evaluation pipeline first.")
    else:
        st.info("Evaluations directory not found. Run the evaluation pipeline first.")

# ==================== About Page ====================

def show_about():
    st.title("ℹ️ About")
    
    st.markdown("""
    ## Conversation Evaluation Benchmark
    
    A production-ready system for evaluating conversations on multiple facets.
    
    ### Features
    - Evaluates on 300+ distinct facets
    - Scalable architecture (supports 5000+ facets)
    - Confidence scores for each evaluation
    - Multiple input formats (manual, samples, JSON)
    - Export capabilities (JSON, CSV)
    
    ### Technology Stack
    - FastAPI (Backend)
    - Streamlit (Frontend)
    - PyTorch & Transformers (LLM)
    - Pandas & NumPy (Data Processing)
    - Docker (Deployment)
    
    ### Architecture
    - Modular design with lazy loading
    - Multi-index facet management
    - Caching and optimization
    - Production-ready API
    
    ### Links
    - [GitHub Repository](#)
    - [API Documentation](#)
    - [Documentation](#)
    """)

# ==================== Main App ====================

def main():
    if page == "Home":
        show_home()
    elif page == "Evaluate Conversation":
        show_evaluate()
    elif page == "Facet Explorer":
        show_facet_explorer()
    elif page == "View Results":
        show_results()
    elif page == "About":
        show_about()

if __name__ == "__main__":
    main()
