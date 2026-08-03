import { existsSync } from 'node:fs'
import { chromium } from 'playwright-core'

const browserCandidates = [
  process.env.CHROME_PATH,
  'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
].filter(Boolean)
const executablePath = browserCandidates.find(existsSync)
if (!executablePath) throw new Error('Chrome 또는 Edge 실행 파일을 찾지 못했습니다.')

const browser = await chromium.launch({ headless: true, executablePath })
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })
const baseUrl = process.env.SMOKE_URL || 'http://127.0.0.1:4173'

try {
  await page.goto(baseUrl, { waitUntil: 'networkidle' })
  await page.getByRole('button', { name: /AI 일정 생성/ }).click()
  await page.waitForURL('**/schedule')
  await page.getByText('오늘의 최적 작업 일정').waitFor()

  await page.getByRole('button', { name: /기상상황 변경 시뮬레이션/ }).click()
  await page.getByText('기상데이터 변경이 감지되었습니다.').waitFor()
  await page.getByRole('button', { name: '일정 다시 계산' }).click()
  await page.getByText('변경된 작업 순서').waitFor({ timeout: 5000 })
  await page.getByText('변경 전·후 일정 비교').waitFor()
  await page.getByText('80%', { exact: true }).first().waitFor()

  await page.getByRole('button', { name: '오늘 일정 확정' }).click()
  await page.getByRole('button', { name: /오늘 일정 확정됨/ }).waitFor()
  await page.getByRole('button', { name: /작업 완료 기록으로 이동/ }).click()

  await page.getByRole('button', { name: /A과원 작업 완료 처리/ }).click()
  await page.getByRole('button', { name: '음성 입력 시작' }).click()
  await page.getByText('말씀하신 내용을 정리했습니다.').waitFor({ timeout: 4000 })
  await page.getByRole('button', { name: '완료 기록 저장' }).click()
  await page.getByRole('button', { name: /A과원 기록 완료/ }).waitFor()

  await page.getByRole('link', { name: '운영센터' }).click()
  await page.getByRole('button', { name: '자동 배치 실행' }).click()
  await page.getByText('25명', { exact: true }).first().waitFor()

  await page.getByRole('link', { name: '주간 계획' }).click()
  await page.getByRole('button', { name: '주간 보기' }).click()
  await page.getByText('이번 주 작업 일정').waitFor()

  await page.getByRole('button', { name: '데모 초기화' }).click()
  await page.waitForURL(baseUrl + '/')
  await page.getByText('좋은 아침입니다, 김농부님').waitFor()
  console.log('통과: AI 생성 → 기상 재계산 → 확정 → 완료 기록 → 센터 배치 → 캘린더 → 초기화')
} finally {
  await browser.close()
}
