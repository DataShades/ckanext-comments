const { watch, src, dest } = require("gulp");

const if_ = require("gulp-if");
const sourcemaps = require("gulp-sourcemaps");
const less = require("gulp-less");
const { resolve } = require("path");

const isDev = () => !!process.env.DEBUG;
const lessFolder = "ckanext/comments/assets/less";
const cssFolder = "ckanext/comments/assets/css";

const buildTask = () =>
  src([resolve(__dirname, lessFolder, "comments-thread.less")])
    .pipe(if_(isDev, sourcemaps.init()))
    .pipe(less())
    .pipe(if_(isDev, sourcemaps.write()))
    .pipe(dest(resolve(__dirname, cssFolder)));

const watchTask = () =>
  watch(
    resolve(__dirname, lessFolder, "*.less"),
    { ignoreInitial: false },
    buildTask
  );

exports.build = buildTask;
exports.watch = watchTask;
