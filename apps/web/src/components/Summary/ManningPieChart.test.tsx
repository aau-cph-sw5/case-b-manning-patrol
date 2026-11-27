// @vitest-environment jsdom
import { cleanup, render, screen } from '@testing-library/react'
import type { ReactNode } from 'react'

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import ManningPieChart, { MANNING_TARGET_PCT } from './ManningPieChart'

interface Slice {
  id: string
  value: number
  label: string
  color: string
}

interface MockPieChartProps {
  width: number
  height: number
  series: {
    data: Slice[]
    startAngle: number
    endAngle: number
    valueFormatter: (item: { value: number }) => string
  }[]
  children?: ReactNode
}

const mocks = vi.hoisted(() => ({
  pieProps: null as MockPieChartProps | null,
  drawingArea: { left: 0, top: 0, width: 100, height: 100 },
}))

vi.mock('@mui/x-charts/PieChart', async () => {
  const { createElement } = await import('react')
  return {
    PieChart: (props: MockPieChartProps) => {
      mocks.pieProps = props
      return createElement('svg', { 'data-testid': 'pie' }, props.children)
    },
  }
})

vi.mock('@mui/x-charts/hooks', () => ({
  useDrawingArea: () => mocks.drawingArea,
}))

function renderPie(percent: number | null, size = 200) {
  const result = render(
    <ManningPieChart title="Alle linjer" percent={percent} size={size} />,
  )
  if (!mocks.pieProps) throw new Error('PieChart was not rendered')
  return {
    ...result,
    props: mocks.pieProps,
    series: mocks.pieProps.series[0],
    slices: mocks.pieProps.series[0].data,
    status: result.container.querySelector('.manning-pie-status'),
    line: result.container.querySelector('line'),
  }
}

function values(slices: Slice[]) {
  return slices.map((slice) => [slice.id, slice.value])
}

beforeEach(() => {
  mocks.pieProps = null
  mocks.drawingArea = { left: 0, top: 0, width: 100, height: 100 }
})

afterEach(() => {
  cleanup()
})

describe('MANNING_TARGET_PCT', () => {
  it('is the 70% compliance rule', () => {
    expect(MANNING_TARGET_PCT).toBe(70)
  })
})

describe('slices', () => {
  it('shows one grey "no data" slice when percent is null', () => {
    const { slices } = renderPie(null)
    expect(slices).toEqual([
      { id: 'none', value: 100, label: 'Ingen data', color: '#d9d9d9' },
    ])
  })

  it('splits manned and unmanned for a normal value', () => {
    const { slices } = renderPie(72)
    expect(values(slices)).toEqual([
      ['manned', 72],
      ['unmanned', 28],
    ])
  })

  it('is all unmanned at 0%', () => {
    const { slices } = renderPie(0)
    expect(values(slices)).toEqual([
      ['manned', 0],
      ['unmanned', 100],
    ])
  })

  it('is all manned at 100%', () => {
    const { slices } = renderPie(100)
    expect(values(slices)).toEqual([
      ['manned', 100],
      ['unmanned', 0],
    ])
  })

  it('clamps values above 100 so unmanned never goes negative', () => {
    const { slices } = renderPie(100.3)
    expect(values(slices)).toEqual([
      ['manned', 100],
      ['unmanned', 0],
    ])
  })

  it('clamps negative values to 0', () => {
    const { slices } = renderPie(-5)
    expect(values(slices)).toEqual([
      ['manned', 0],
      ['unmanned', 100],
    ])
  })

  it.each([0, 0.4, 33.3, 69.9, 70, 99.99, 100])(
    'slices add up to 100 at %s%%',
    (percent) => {
      const { slices } = renderPie(percent)
      const total = slices.reduce((sum, slice) => sum + slice.value, 0)
      expect(total).toBeCloseTo(100)
    },
  )

  it('colours manned green and unmanned red', () => {
    const { slices } = renderPie(50)
    expect(slices.map((slice) => slice.color)).toEqual(['#8fdca8', '#f5a3a3'])
  })
})

describe('status text', () => {
  it('says there is no running time when percent is null', () => {
    const { status } = renderPie(null)
    expect(status?.textContent).toBe('Ingen køretid endnu')
    expect(status?.classList.contains('ok')).toBe(false)
    expect(status?.classList.contains('low')).toBe(false)
  })

  it('is below target at 0%', () => {
    const { status } = renderPie(0)
    expect(status?.textContent).toBe('0% bemandet · under målet på 70%')
    expect(status?.classList.contains('low')).toBe(true)
  })

  it('meets the target at exactly 70%', () => {
    const { status } = renderPie(70)
    expect(status?.textContent).toBe('70% bemandet · mål på 70% opnået')
    expect(status?.classList.contains('ok')).toBe(true)
  })

  it('is below target just under 70%', () => {
    const { status } = renderPie(69.99)
    expect(status?.classList.contains('low')).toBe(true)
  })

  it('never shows 70% while below target', () => {
    const { status } = renderPie(69.6)
    expect(status?.textContent).toBe('69% bemandet · under målet på 70%')
  })

  it('meets the target at 100%', () => {
    const { status } = renderPie(100)
    expect(status?.textContent).toBe('100% bemandet · mål på 70% opnået')
    expect(status?.classList.contains('ok')).toBe(true)
  })

  it('shows a clamped value above 100 as 100%', () => {
    const { status } = renderPie(100.3)
    expect(status?.textContent).toBe('100% bemandet · mål på 70% opnået')
  })
})

describe('chart setup', () => {
  it('uses size for both width and height', () => {
    const { props } = renderPie(50, 160)
    expect(props.width).toBe(160)
    expect(props.height).toBe(160)
  })

  it('starts at 12 o\'clock and goes a full turn, as TargetMarker assumes', () => {
    const { series } = renderPie(50)
    expect(series.startAngle).toBe(0)
    expect(series.endAngle).toBe(360)
  })

  it('formats tooltip values with one decimal and a percent sign', () => {
    const { series } = renderPie(72.44)
    expect(series.valueFormatter({ value: 72.44 })).toBe('72.4%')
    expect(series.valueFormatter({ value: 0 })).toBe('0.0%')
  })

  it('renders a JSX title', () => {
    render(
      <ManningPieChart
        title={<><span>M1</span>/<span>M2</span></>}
        percent={50}
        size={160}
      />,
    )
    expect(screen.getByText('M1')).toBeTruthy()
    expect(screen.getByText('M2')).toBeTruthy()
  })
})

describe('TargetMarker', () => {
  function coords(line: Element | null) {
    if (!line) throw new Error('No target line rendered')
    return ['x1', 'y1', 'x2', 'y2'].map((name) => Number(line.getAttribute(name)))
  }

  it('starts in the centre of the drawing area', () => {
    const { line } = renderPie(50)
    const [x1, y1] = coords(line)
    expect(x1).toBe(50)
    expect(y1).toBe(50)
  })

  it('ends on the circle at 70% clockwise from 12 o\'clock (252°)', () => {
    const { line } = renderPie(50)
    const [, , x2, y2] = coords(line)
    /** 252° is lower left: sin(252°) ≈ -0.951, cos(252°) ≈ -0.309, r = 50. */
    expect(x2).toBeCloseTo(50 - 47.553, 2)
    expect(y2).toBeCloseTo(50 + 15.451, 2)
  })

  it('uses the offset and the shortest side for a non-square area', () => {
    mocks.drawingArea = { left: 10, top: 20, width: 200, height: 100 }
    const { line } = renderPie(50)
    const [x1, y1, x2, y2] = coords(line)
    expect(x1).toBe(110)
    expect(y1).toBe(70)
    expect(x2).toBeCloseTo(110 - 47.553, 2)
    expect(y2).toBeCloseTo(70 + 15.451, 2)
  })

  it('is dashed', () => {
    const { line } = renderPie(50)
    expect(line?.getAttribute('stroke-dasharray')).toBe('6 4')
  })

  it('is drawn even when there is no data', () => {
    const { line } = renderPie(null)
    expect(line).not.toBeNull()
  })
})
