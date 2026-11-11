<?php
// Brings every .mp3 in a folder to the same loudness (EBU R128, two-pass ffmpeg loudnorm).
// Usage: php normalize-sounds.php <input folder> [output folder]
// Needs ffmpeg on the PATH. Originals are not touched; results go to <input>/normalized.

$in = $argv[1] ?? null;
if (!$in || !is_dir($in)) { fwrite(STDERR, "Usage: php normalize-sounds.php <input folder> [output folder]\n"); exit(1); }
$out = $argv[2] ?? ($in . DIRECTORY_SEPARATOR . 'normalized');
if (!is_dir($out)) mkdir($out, 0777, true);

$target = 'I=-16:TP=-1.5:LRA=11'; // loudness -16 LUFS, peaks at most -1.5 dBTP

foreach (glob($in . DIRECTORY_SEPARATOR . '*.mp3') as $file) {
    $name = basename($file);
    $src = escapeshellarg($file);

    // pass 1: measure
    $log = shell_exec("ffmpeg -hide_banner -nostats -i $src -af loudnorm=$target:print_format=json -f null - 2>&1");
    if (!preg_match('/\{[^{}]*"input_i"[^{}]*\}/s', $log ?? '', $m)) { echo "skip (could not measure): $name\n"; continue; }
    $j = json_decode($m[0], true);

    // pass 2: apply with the measured values
    $af = sprintf('loudnorm=%s:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true',
        $target, $j['input_i'], $j['input_tp'], $j['input_lra'], $j['input_thresh'], $j['target_offset']);
    $dst = escapeshellarg($out . DIRECTORY_SEPARATOR . $name);
    exec("ffmpeg -hide_banner -loglevel error -y -i $src -af " . escapeshellarg($af) . " -ar 44100 -c:a libmp3lame -q:a 2 $dst", $o, $code);
    echo ($code === 0 ? "ok   " : "FAIL ") . "$name (was {$j['input_i']} LUFS)\n";
}
