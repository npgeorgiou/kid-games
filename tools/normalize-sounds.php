<?php
// Brings every .mp3 in a folder to the same loudness: -16 LUFS (EBU R128), true peaks at most -1.5 dBTP.
// Usage: php normalize-sounds.php [input folder, default current] [output folder]
// Needs ffmpeg on the PATH. Originals are not touched; results go to <input>/normalized.
//
// How: measure the loudness, change the volume by one fixed amount (no compression), and only if
// that pushes the loudest peaks over -1.5 dBTP, a peak limiter trims those peaks. Then measure again
// and correct the volume and the limiter (up to 25 rounds) until the file is within 0.3 LU of -16
// and its peaks are at most -1.5 dBTP.
// Sounds shorter than the 0.4 s that loudness measuring needs are measured with silence added after
// them (silence does not count towards loudness), and the silence is cut off again.
// (The old version used ffmpeg loudnorm: it could not measure very short sounds, and when a sound's
// peaks were too high it switched to its compressing mode, which made those sounds harsh and loud.)

$in = $argv[1] ?? '.';
if (!is_dir($in)) { fwrite(STDERR, "Usage: php normalize-sounds.php <input folder> [output folder]\n"); exit(1); }
$out = $argv[2] ?? ($in . DIRECTORY_SEPARATOR . 'normalized');
if (!is_dir($out)) mkdir($out, 0777, true);

const TARGET_I = -16.0;  // LUFS
const TARGET_TP = -1.5;  // dBTP

// loudness (LUFS) and true peak (dBTP) of a file, measured with 1 s of silence added
function measure($file) {
    $src = escapeshellarg($file);
    $log = shell_exec("ffmpeg -hide_banner -nostats -i $src -af apad=pad_dur=1,ebur128=peak=true -f null - 2>&1") ?? '';
    if (!preg_match('/Summary:.*?I:\s*(-?[\d.]+|-inf)\s*LUFS.*?Peak:\s*(-?[\d.]+|-inf)\s*dBFS/s', $log, $m)) return null;
    if ($m[1] === '-inf') return null;
    return [floatval($m[1]), floatval($m[2])];
}

function render($src, $dst, $gainDb, $dur, $ceilDb) {
    // volume, then a true-peak limiter (oversampled 4x) only touching peaks over TARGET_TP
    $lim = pow(10, $ceilDb / 20);
    $af = sprintf('volume=%.3fdB,aresample=176400,alimiter=limit=%.5f:attack=0.5:release=20:level=disabled,aresample=44100,atrim=0:%.4f',
        $gainDb, $lim, $dur);
    exec('ffmpeg -hide_banner -loglevel error -y -i ' . escapeshellarg($src) . ' -af ' . escapeshellarg($af)
        . ' -ar 44100 -c:a libmp3lame -q:a 2 ' . escapeshellarg($dst), $o, $code);
    return $code === 0;
}

foreach (glob($in . DIRECTORY_SEPARATOR . '*.mp3') as $file) {
    $name = basename($file);
    $dst = $out . DIRECTORY_SEPARATOR . $name;
    $m = measure($file);
    if (!$m) { echo "FAIL (could not measure): $name\n"; continue; }
    $dur = floatval(trim(shell_exec('ffprobe -v error -show_entries format=duration -of csv=p=0 ' . escapeshellarg($file))));
    $gain = TARGET_I - $m[0];
    $ceil = TARGET_TP - 0.6; // the mp3 encoding raises peaks a little, so the limiter aims lower
    $ok = false;
    for ($round = 0; $round < 25; $round++) {
        if (!render($file, $dst, $gain, $dur, $ceil)) break;
        $r = measure($dst);
        if (!$r) break;
        if (abs($r[0] - TARGET_I) <= 0.3 && $r[1] <= TARGET_TP) { $ok = true; break; }
        $gain += TARGET_I - $r[0];
        if ($r[1] > TARGET_TP) $ceil -= $r[1] - TARGET_TP + 0.1;
    }
    echo ($ok ? "ok   " : "FAIL ") . sprintf("%s (was %.1f LUFS, now %.1f LUFS, peak %.1f dBTP)\n", $name, $m[0], $r[0] ?? NAN, $r[1] ?? NAN);
}
