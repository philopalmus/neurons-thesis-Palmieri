set term pngcairo enhanced dashed
set output "spikes3-5.5-1-0.5.png"
set xrange [0:300]
set yrange [0:500]
plot \
50 title "" with lines dt 2 lw 1 lc rgb "black",\
100 title "" with lines dt 2 lw 1 lc rgb "black",\
150 title "" with lines dt 2 lw 1 lc rgb "black",\
200 title "" with lines dt 2 lw 1 lc rgb "black",\
250 title "" with lines dt 2 lw 1 lc rgb "black",\
300 title "" with lines dt 2 lw 1 lc rgb "black",\
350 title "" with lines dt 2 lw 1 lc rgb "black",\
400 title "" with lines dt 2 lw 1 lc rgb "black",\
450 title "" with lines dt 2 lw 1 lc rgb "black",\
"spikes3-5.5-1-0.5.dat" using 1:4 title "" with points pt 7 ps 1 lc rgb "red"
