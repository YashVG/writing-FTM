"""Run upstream CLI and expose the MLX allocation peak hidden by its UI."""
import json
import mlx.core as mx
from mlx_lm.lora import main
main()
print(json.dumps({'mlx_peak_memory_gb':mx.get_peak_memory()/1e9}),flush=True)
