import os
import sys
from core.models import PlanningRequest
from core.pipeline import PlanningPipeline

def run_test():
    print("Initializing Planning Pipeline (including KnowledgeLoader)...")
    pipeline = PlanningPipeline()
    
    req = PlanningRequest(
        project_name="Phase9-Test",
        prompt="Design a secure payment processing API that handles 10,000 TPS.",
        cloud_target="AWS",
        compliance="PCI-DSS",
        model="claude-4-sonnet"
    )
    
    print("\nRunning pipeline...\n")
    for state in pipeline.run(req):
        status = state.get('status')
        agent = state.get('agent', 'System')
        if status == 'running':
            print(f"[{agent}] is running...")
        elif status == 'complete':
            print(f"[{agent}] completed!")
        elif status == 'error':
            print(f"[{agent}] ERROR: {state.get('error')}")
            sys.exit(1)
        elif status == 'finished':
            metrics = state.get('metrics', {})
            print("\n=== PIPELINE FINISHED ===")
            print(f"Blueprint Score: {metrics.get('blueprint_score')}")
            print(f"Total Time: {metrics.get('total_latency_ms', 0) / 1000.0}s")
            print(f"Est. Cost: ${metrics.get('estimated_cost_usd', 0):.4f}")
            print("=========================")

if __name__ == "__main__":
    run_test()
