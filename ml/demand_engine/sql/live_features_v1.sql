-- Beyond Demand Engine v1 — live inventory feature query
-- Parameter: :ticket_event_id
--
-- IMPORTANT SEMANTICS
-- * Public availability is a demand proxy, NOT confirmed ticket sales.
-- * A decrease in matched available inventory is called absorption, not sale.
-- * Sectors entering/leaving the public response are tracked separately so
--   coverage changes do not silently masquerade as demand.

WITH event_snapshots AS (
    SELECT
        s.id AS snapshot_id,
        s.ticket_event_id,
        s.captured_at,
        s.available_total,
        s.sector_count,
        LAG(s.id) OVER w AS previous_snapshot_id,
        LAG(s.captured_at) OVER w AS previous_captured_at,
        LAG(s.available_total) OVER w AS previous_available_total,
        FIRST_VALUE(s.available_total) OVER w_full AS first_available_total
    FROM snapshots s
    WHERE s.ticket_event_id = :ticket_event_id
      AND s.available_total IS NOT NULL
    WINDOW
        w AS (
            PARTITION BY s.ticket_event_id
            ORDER BY s.captured_at, s.id
        ),
        w_full AS (
            PARTITION BY s.ticket_event_id
            ORDER BY s.captured_at, s.id
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        )
),
pairs AS (
    SELECT
        es.*,
        EXTRACT(EPOCH FROM (es.captured_at - es.previous_captured_at)) / 3600.0
            AS elapsed_hours
    FROM event_snapshots es
    WHERE es.previous_snapshot_id IS NOT NULL
),
sector_universe AS (
    SELECT
        p.snapshot_id,
        p.previous_snapshot_id,
        p.ticket_event_id,
        p.captured_at,
        p.previous_captured_at,
        p.elapsed_hours,
        p.available_total,
        p.previous_available_total,
        p.first_available_total,
        p.sector_count,
        sectors.sector
    FROM pairs p
    CROSS JOIN LATERAL (
        SELECT si.sector
        FROM sector_inventory si
        WHERE si.snapshot_id = p.snapshot_id

        UNION

        SELECT si.sector
        FROM sector_inventory si
        WHERE si.snapshot_id = p.previous_snapshot_id
    ) sectors
),
sector_pairs AS (
    SELECT
        u.*,
        prev.available AS previous_sector_available,
        cur.available AS current_sector_available,
        CASE
            WHEN prev.sector IS NOT NULL AND cur.sector IS NOT NULL THEN 'matched'
            WHEN prev.sector IS NULL AND cur.sector IS NOT NULL THEN 'entered'
            WHEN prev.sector IS NOT NULL AND cur.sector IS NULL THEN 'left'
        END AS sector_state
    FROM sector_universe u
    LEFT JOIN sector_inventory cur
        ON cur.snapshot_id = u.snapshot_id
       AND cur.sector = u.sector
    LEFT JOIN sector_inventory prev
        ON prev.snapshot_id = u.previous_snapshot_id
       AND prev.sector = u.sector
),
transition_summary AS (
    SELECT
        snapshot_id,
        previous_snapshot_id,
        ticket_event_id,
        captured_at,
        previous_captured_at,
        elapsed_hours,
        available_total,
        previous_available_total,
        first_available_total,
        sector_count,

        COUNT(*) FILTER (WHERE sector_state = 'matched') AS matched_sector_count,
        COUNT(*) FILTER (WHERE sector_state = 'entered') AS entered_sector_count,
        COUNT(*) FILTER (WHERE sector_state = 'left') AS left_sector_count,

        COALESCE(
            SUM(GREATEST(previous_sector_available - current_sector_available, 0))
            FILTER (WHERE sector_state = 'matched'),
            0
        ) AS matched_absorption,

        COALESCE(
            SUM(GREATEST(current_sector_available - previous_sector_available, 0))
            FILTER (WHERE sector_state = 'matched'),
            0
        ) AS matched_release,

        COALESCE(
            SUM(current_sector_available) FILTER (WHERE sector_state = 'entered'),
            0
        ) AS entered_available,

        COALESCE(
            SUM(previous_sector_available) FILTER (WHERE sector_state = 'left'),
            0
        ) AS left_available
    FROM sector_pairs
    GROUP BY
        snapshot_id,
        previous_snapshot_id,
        ticket_event_id,
        captured_at,
        previous_captured_at,
        elapsed_hours,
        available_total,
        previous_available_total,
        first_available_total,
        sector_count
),
base AS (
    SELECT
        t.*,
        matched_absorption - matched_release AS matched_net_absorption,
        entered_available - left_available AS coverage_inventory_effect,
        previous_available_total - available_total AS raw_net_removed_since_previous,
        first_available_total - available_total AS raw_net_removed_since_first
    FROM transition_summary t
),
rolling AS (
    SELECT
        b.*,
        SUM(matched_net_absorption) OVER w6 AS matched_net_removed_6h,
        SUM(elapsed_hours) OVER w6 AS elapsed_6h,
        SUM(matched_net_absorption) OVER w24 AS matched_net_removed_24h,
        SUM(elapsed_hours) OVER w24 AS elapsed_24h
    FROM base b
    WINDOW
        w6 AS (
            PARTITION BY ticket_event_id
            ORDER BY captured_at
            RANGE BETWEEN INTERVAL '6 hours' PRECEDING AND CURRENT ROW
        ),
        w24 AS (
            PARTITION BY ticket_event_id
            ORDER BY captured_at
            RANGE BETWEEN INTERVAL '24 hours' PRECEDING AND CURRENT ROW
        )
)
SELECT
    snapshot_id,
    previous_snapshot_id,
    ticket_event_id,
    captured_at,
    previous_captured_at,
    ROUND(elapsed_hours::numeric, 3) AS elapsed_hours,

    available_total,
    previous_available_total,
    first_available_total,
    sector_count,
    ROUND((available_total::numeric / NULLIF(first_available_total, 0))::numeric, 6)
        AS available_index,

    raw_net_removed_since_first AS net_removed_since_first,
    raw_net_removed_since_previous AS net_removed_since_previous,
    ROUND((raw_net_removed_since_previous / NULLIF(elapsed_hours, 0))::numeric, 3)
        AS velocity_since_previous,

    matched_sector_count,
    entered_sector_count,
    left_sector_count,
    matched_absorption,
    matched_release,
    matched_net_absorption,
    entered_available,
    left_available,
    coverage_inventory_effect,

    matched_net_removed_6h AS net_removed_6h,
    ROUND((matched_net_removed_6h / NULLIF(elapsed_6h, 0))::numeric, 3)
        AS velocity_6h,
    matched_net_removed_24h AS net_removed_24h,
    ROUND((matched_net_removed_24h / NULLIF(elapsed_24h, 0))::numeric, 3)
        AS velocity_24h,
    ROUND((
        (matched_net_removed_6h / NULLIF(elapsed_6h, 0))
        - (matched_net_removed_24h / NULLIF(elapsed_24h, 0))
    )::numeric, 3) AS acceleration_6h_vs_24h,

    (entered_sector_count > 0 OR left_sector_count > 0) AS sector_coverage_change_flag,
    (matched_release > 0) AS release_activity_flag,
    'demand_proxy_not_confirmed_sales'::text AS inventory_interpretation
FROM rolling
ORDER BY captured_at;
