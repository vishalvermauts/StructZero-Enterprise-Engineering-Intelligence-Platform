import argparse
import sys
from core.models import PlanningRequest
from core.pipeline import PlanningPipeline
from core.model_router import MODEL_ROUTER
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)

def main():
    parser = argparse.ArgumentParser(description="StructZero Enterprise CoCo CLI")
    parser.add_argument("--prompt", type=str, required=True, help="The architecture prompt")
    parser.add_argument("--compliance", type=str, default="PCI-DSS", help="Compliance target (e.g. PCI-DSS, HIPAA)")
    parser.add_argument("--cloud", type=str, default="AWS", help="Cloud target (e.g. AWS, GCP, Azure)")
    parser.add_argument("--project", type=str, default="CLI_Demo_Project", help="Project name")
    parser.add_argument("--out", type=str, default="blueprint.md", help="Output file for the generated blueprint")

    args = parser.parse_args()

    print(f"{Fore.CYAN}{Style.BRIGHT}==========================================")
    print(f"{Fore.CYAN}{Style.BRIGHT} StructZero Enterprise CoCo - Cortex CLI")
    print(f"{Fore.CYAN}{Style.BRIGHT}==========================================")
    print(f"Project:    {args.project}")
    print(f"Cloud:      {args.cloud}")
    print(f"Compliance: {args.compliance}")
    print(f"Prompt:     {args.prompt}")
    print(f"{Fore.CYAN}==========================================\n")

    # Create the request
    request = PlanningRequest(
        project_name=args.project,
        prompt=args.prompt,
        cloud_target=args.cloud,
        compliance=args.compliance,
        model=MODEL_ROUTER["architect"]
    )

    print(f"{Fore.YELLOW}[*] Initializing Pipeline and Storage...")
    pipeline = PlanningPipeline()
    
    print(f"{Fore.YELLOW}[*] Executing Multi-Agent Orchestration via Cortex...\n")
    
    # Track states to prevent spamming
    agent_status = {}

    final_blueprint = None

    try:
        for update in pipeline.run(request):
            agent = update.get("agent", "System")
            status = update.get("status", "unknown")
            step = update.get("step", 0)

            if status == "running":
                # Only print running once per agent step
                if agent_status.get(agent) != "running":
                    print(f"{Fore.MAGENTA}  ⏳ [Step {step}] {agent} is processing...")
                    agent_status[agent] = "running"
            elif status == "complete":
                if "time" in update:
                    print(f"{Fore.GREEN}  ✅ [Step {step}] {agent} completed in {update['time']:.2f}s")
                else:
                    print(f"{Fore.GREEN}  ✅ [Step {step}] {agent} completed")
                
                if "citations" in update:
                    print(f"{Fore.LIGHTBLACK_EX}      => Found {len(update['citations'])} relevant knowledge snippets.")
                    
                if "output" in update and "Voter" in agent:
                    vote = str(update["output"]).strip().splitlines()[0] if update["output"] else "UNKNOWN"
                    print(f"{Fore.LIGHTBLACK_EX}      => Vote: {vote}")
                    
                if "validation" in update:
                    val = update["validation"]
                    # val is a dataclass, so we access attributes
                    print(f"{Fore.LIGHTBLACK_EX}      => Verdict: {val.status} | Score: {val.overall_score} | Board: {val.board_decision}")
            elif status == "error":
                print(f"{Fore.RED}  ❌ [Step {step}] {agent} ERROR: {update.get('error', '')}")
                sys.exit(1)
            elif status == "finished":
                final_blueprint = update.get("blueprint")
                metrics = update.get("metrics")
                print(f"\n{Fore.GREEN}{Style.BRIGHT}🎉 Workflow Complete!")
                if metrics:
                    print(f"{Fore.CYAN}Validation Score: {metrics.get('blueprint_score', 0)}/100")
                    print(f"{Fore.CYAN}Board Decision:   {metrics.get('board_decision', 'N/A')}")
                    print(f"{Fore.CYAN}Total Time:       {metrics.get('total_latency_ms', 0)/1000:.2f}s")
                    print(f"{Fore.CYAN}Cortex Calls:     {metrics.get('cortex_calls', 0)}")
                    print(f"{Fore.CYAN}Estimated Cost:   ${metrics.get('estimated_cost_usd', 0):.4f}")
    except Exception as e:
        print(f"\n{Fore.RED}Pipeline execution failed: {e}")
        sys.exit(1)

    if final_blueprint and final_blueprint.raw_markdown:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(final_blueprint.raw_markdown)
        print(f"\n{Fore.GREEN}Blueprint successfully written to {Style.BRIGHT}{args.out}{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.RED}Failed to generate blueprint content.")

if __name__ == "__main__":
    main()
