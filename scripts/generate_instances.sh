batch_dir=data/dial_generations/

python self_instruct/generate_instances.py \
    --batch_dir ${batch_dir} \
    --input_file machine_generated_instructions.jsonl \
    --output_file machine_generated_instances.jsonl \
    --max_instances_to_gen 1 \
    --engine "gpt-3.5-turbo" \
    --request_batch_size 1 \
    --api_key "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"