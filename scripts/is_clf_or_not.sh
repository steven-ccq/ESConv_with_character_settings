batch_dir=data/dial_generations/

python self_instruct/identify_clf_or_not.py \
    --batch_dir ${batch_dir} \
    --engine "gpt-3.5-turbo" \
    --request_batch_size 1 \
    --api_key "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"