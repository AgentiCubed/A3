#!/usr/bin/env Rscript
# AgentiCubed R analysis worker.
#
# Job interface (language-neutral, so the domain never depends on R):
#   stdin  : nothing
#   args   : <csv_path> <value_column>
#   stdout : a single JSON object {"n","mean","sd","min","max","sum"}
#   exit   : 0 on success, non-zero on error (message on stderr)
#
# Invoked by app/analysis/r_worker.py when Rscript is available.

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 2) {
  write("usage: summary.R <csv_path> <value_column>", stderr())
  quit(status = 2)
}

csv_path <- args[[1]]
value_col <- args[[2]]

df <- tryCatch(read.csv(csv_path, stringsAsFactors = FALSE),
               error = function(e) { write(conditionMessage(e), stderr()); quit(status = 1) })

if (!(value_col %in% names(df))) {
  write(paste("column not found:", value_col), stderr())
  quit(status = 1)
}

x <- suppressWarnings(as.numeric(df[[value_col]]))
x <- x[!is.na(x)]

n <- length(x)
mean_v <- if (n > 0) round(mean(x), 4) else 0
sd_v <- if (n > 1) round(sd(x), 4) else 0
min_v <- if (n > 0) min(x) else 0
max_v <- if (n > 0) max(x) else 0
sum_v <- sum(x)

cat(sprintf(
  '{"n":%d,"mean":%s,"sd":%s,"min":%s,"max":%s,"sum":%s}',
  n, mean_v, sd_v, min_v, max_v, sum_v
))
