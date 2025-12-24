import pytest
import os
import shutil

@pytest.fixture
def sample_pwx_content():
    return """<?xml version="1.0" encoding="utf-8"?>
<pwx version="1.0" xmlns="http://www.peaksware.com/PWX/1/0">
  <workout>
    <time>2025-12-03T05:48:22</time>
    <summarydata>
      <duration>60</duration>
    </summarydata>
    <sample>
      <timeoffset>0</timeoffset>
      <alt>100</alt>
      <dist>0</dist>
      <hr>120</hr>
      <cad>80</cad>
      <pwr>200</pwr>
      <spd>10</spd>
    </sample>
    <sample>
      <timeoffset>30</timeoffset>
      <alt>105</alt>
      <dist>100</dist>
      <hr>130</hr>
      <cad>85</cad>
      <pwr>210</pwr>
      <spd>11</spd>
    </sample>
    <sample>
      <timeoffset>60</timeoffset>
      <alt>110</alt>
      <dist>200</dist>
      <hr>140</hr>
      <cad>90</cad>
      <pwr>220</pwr>
      <spd>12</spd>
    </sample>
  </workout>
</pwx>"""

@pytest.fixture
def tmp_pwx_file(tmp_path, sample_pwx_content):
    p = tmp_path / "test.pwx"
    p.write_text(sample_pwx_content)
    return str(p)

@pytest.fixture
def setup_test_dirs(tmp_path):
    orig = tmp_path / "original"
    conv = tmp_path / "converted"
    proc = tmp_path / "processed"
    fail = tmp_path / "failed"
    
    orig.mkdir()
    conv.mkdir()
    proc.mkdir()
    fail.mkdir()
    
    return {
        "base": str(tmp_path),
        "original": str(orig),
        "converted": str(conv),
        "processed": str(proc),
        "failed": str(fail)
    }
