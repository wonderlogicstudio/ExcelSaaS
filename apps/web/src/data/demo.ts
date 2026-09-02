import type { ScanResult } from '../types';
import demoFixture from './demo-result.fixture.json';

interface DemoFixture {
  fixture_metadata: {
    generated_at: string;
    generated_from: string;
    generator: string;
    scanner_version: string;
    rule_set_version: string;
  };
  scan_result: ScanResult;
}

export const demoFixtureMetadata = (demoFixture as DemoFixture).fixture_metadata;
export const demoResult: ScanResult = (demoFixture as DemoFixture).scan_result;
