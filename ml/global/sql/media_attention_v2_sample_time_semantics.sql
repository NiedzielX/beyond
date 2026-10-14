-- Media Attention v2 uses the GDELT source-file timestamp as the sample time.
-- This keeps rolling 24h / previous-24h windows on one consistent time basis.

update public.media_attention_samples_v2
set sample_at=source_file_timestamp
where sample_at<>source_file_timestamp;

select public.refresh_media_attention_context_v02();
select public.refresh_hype_challenger_v1();
