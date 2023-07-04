batch_dir=data/dial_generations/

python self_instruct/bootstrap_instructions.py \
    --batch_dir ${batch_dir} \
    --num_instructions_to_generate 100 \
    --seed_tasks_path ./seeds.jsonl \
    --engine "gpt-3.5-turbo" \
    --api_key "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"