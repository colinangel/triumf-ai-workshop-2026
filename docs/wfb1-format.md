# WFB1 raw waveform format

A minimal DAQ-style binary used by the C++ challenge. All integers are
little-endian. Records are **packed**: there is no padding between fields.

## File header (24 bytes)

| Offset | Type      | Field        | Notes                          |
|-------:|-----------|--------------|--------------------------------|
| 0      | char[4]   | `magic`      | ASCII `WFB1`                   |
| 4      | uint16    | `version`    | currently 1                    |
| 6      | uint16    | `n_channels` |                                |
| 8      | uint32    | `n_samples`  | samples per channel per event  |
| 12     | uint32    | `dt_ps`      | sample period, picoseconds     |
| 16     | uint64    | `n_events`   |                                |

## Each event

Event header (14 bytes), then `n_channels * n_samples` samples.

| Offset | Type   | Field             | Notes                                  |
|-------:|--------|-------------------|----------------------------------------|
| 0      | uint32 | `event_id`        | 0, 1, 2, ...                           |
| 4      | uint16 | `flags`           | bit c set = channel c saturated        |
| 6      | uint64 | `trigger_time_ps` | trigger time stamp                     |

Samples: uint16 ADC counts, channel-major (all of channel 0, then channel 1).

## Reference quantities for the challenge

For each event and channel:

* `baseline_adc`: arithmetic mean of samples 0 to 99, as a floating-point number
* `charge_adc_samples`: sum over samples 120 to 199 of (`baseline_adc` - sample)

Generate a file with `uv run wfkit export-wfb1` (writes `data/raw/run_sipm.wfb1`
plus a matching Parquet file and truth table).
