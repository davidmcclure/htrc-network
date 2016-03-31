package main

import (
	"compress/bzip2"
	"github.com/bitly/go-simplejson"
	"github.com/jawher/mow.cli"
	"github.com/stretchr/powerwalk"
	"os"
	"runtime"
	"strconv"
	"sync"
	"sync/atomic"
)

func main() {

	runtime.GOMAXPROCS(runtime.NumCPU())

	app := cli.App("hol", "The history of literature.")

	app.Command(
		"yearCounts",
		"Extract per-year total counts",
		func(cmd *cli.Cmd) {

			var corpus = cmd.StringArg(
				"CORPUS",
				"path/to/htrc",
				"HTRC root",
			)

			cmd.Action = func() {
				extractYearCounts(*corpus)
			}

		},
	)

	app.Run(os.Args)

}

// Accumulate per-year token counts.
func extractYearCounts(path string) {

	counts := make(map[int]int)

	var mutex = &sync.Mutex{}

	var ops int64 = 0

	powerwalk.Walk(path, func(path string, info os.FileInfo, _ error) error {

		if !info.IsDir() {

			vol, err := NewVolumeFromPath(path)
			if err != nil {
				return err
			}

			// Increment the year count.
			mutex.Lock()
			counts[vol.Year()] += vol.TokenCount()
			mutex.Unlock()

			// Log progress.
			atomic.AddInt64(&ops, 1)
			if ops%100 == 0 {
				println(ops)
			}

		}

		return nil

	})

}

// Dump year counts to disk.
func dumpYearCounts(counts map[int]int) {
	// TODO
}

// Given a path for a .bz2 JSON file in the HTRC corpus, decode the file and
// parse the JSON into a Volume.
func NewVolumeFromPath(path string) (*Volume, error) {

	deflated, err := os.Open(path)
	if err != nil {
		return nil, err
	}

	defer deflated.Close()

	inflated := bzip2.NewReader(deflated)

	parsed, err := simplejson.NewFromReader(inflated)
	if err != nil {
		return nil, err
	}

	return &Volume{json: parsed}, nil

}

// An individual HTRC volume.
type Volume struct {
	json *simplejson.Json
}

// Get the HTRC id.
func (v *Volume) Id() string {
	return v.json.Get("id").MustString()
}

// Get the year, 0 if parse fails.
func (v *Volume) Year() int {

	ystr := v.json.GetPath("metadata", "pubDate").MustString()

	yint, err := strconv.Atoi(ystr)
	if err != nil {
		return 0
	}

	return yint

}

// Make page instances.
func (v *Volume) Pages() []*Page {

	key := v.json.GetPath("features", "pages")

	var pages []*Page

	for i, _ := range key.MustArray() {
		json := key.GetIndex(i)
		pages = append(pages, &Page{json: json})
	}

	return pages

}

// Get the total token count for all pages.
func (v *Volume) TokenCount() int {

	count := 0
	for _, page := range v.Pages() {
		count += page.TokenCount()
	}

	return count

}

// An individual page.
type Page struct {
	json *simplejson.Json
}

// Get the token count for the page body.
func (p *Page) TokenCount() int {
	return p.json.GetPath("body", "tokenCount").MustInt()
}
