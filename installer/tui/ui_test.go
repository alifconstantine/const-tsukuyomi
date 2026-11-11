package main

import (
	"charm.land/lipgloss/v2"
	"github.com/charmbracelet/x/ansi"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestWizardKeepsCardAnchoredAcrossSteps(t *testing.T) {
	for _, size := range [][2]int{{120, 40}, {100, 30}, {80, 24}} {
		m := model{state: "wizard", w: size[0], h: size[1], enterPos: 1, picks: map[string]string{}, flow: []step{
			{key: "short", title: "Short page", kind: kNotice, desc: []string{"One row."}},
			{key: "long", title: "Long page", kind: kNotice, desc: []string{strings.Repeat("More content to explain. ", 20)}},
			{key: "name", title: "Hostname", kind: kInput, placeholder: "tsukuyomi"},
		}}
		var expected []int
		for at := range m.flow {
			m.idx = at
			rendered := ansi.Strip(m.fittedFrame())
			if lipgloss.Width(rendered) > m.w || lipgloss.Height(rendered) > m.h {
				t.Fatalf("overflow at %v", size)
			}
			var borders []int
			for y, line := range strings.Split(rendered, "\n") {
				if strings.ContainsAny(line, "╭╰┌└") {
					borders = append(borders, y)
				}
			}
			if at == 0 {
				expected = borders
			} else if !equalRows(expected, borders) {
				t.Fatalf("card moved at %v: %v -> %v", size, expected, borders)
			}
		}
	}
}
func equalRows(a, b []int) bool {
	if len(a) != len(b) || len(a) == 0 {
		return false
	}
	for i := range a {
		if a[i] != b[i] {
			return false
		}
	}
	return true
}
func TestFailurePreservesCauseWithoutOversizedHelp(t *testing.T) {
	t.Setenv("TMPDIR", t.TempDir())
	m := model{w: 100, h: 30, installLog: []string{"error: failed retrieving package", "Installation stopped: Could not download or verify the installation packages.", "exit status 1"}}
	m.failInstall("Downloading and verifying signed packages")
	contents, err := os.ReadFile(m.logPath)
	if err != nil || !strings.Contains(string(contents), "failed retrieving") {
		t.Fatalf("missing backend log: %v", err)
	}
	st, _ := os.Stat(m.logPath)
	if st.Mode().Perm() != 0600 {
		t.Fatal("installer log must be private")
	}
	if filepath.Base(m.logPath) != "install.log" {
		t.Fatal("incorrect log path")
	}
	view := ansi.Strip(m.viewFailed())
	if !strings.Contains(view, "Could not download or verify") || !strings.Contains(view, "No disk writes") {
		t.Fatal("missing cause/recovery")
	}
	if lipgloss.Height(view) > m.h-2 {
		t.Fatal("failure page overflows")
	}
}
func TestFailureCannotRestartAfterStorageStarted(t *testing.T) {
	m := model{state: "failed", partitioned: true}
	result, cmd := m.onKey("r")
	if result.(model).state != "failed" || cmd != nil {
		t.Fatal("partially written disk must not be automatically retried")
	}
}

func TestReviewCannotAcceptBlindConfirmationOnShortScreen(t *testing.T) {
	m := model{state: "wizard", w: 80, h: 18, yes: true, flow: []step{{key: "review", kind: kConfirm}}}
	result, cmd := m.onKey("enter")
	if result.(model).state != "wizard" || cmd != nil {
		t.Fatal("installer accepted a hidden confirmation")
	}
}
