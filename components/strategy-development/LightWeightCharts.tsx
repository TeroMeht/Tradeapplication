"use client";

import React, { useEffect, useRef } from "react";
import { createChart, HistogramSeries, LineSeries, CandlestickSeries } from "lightweight-charts";

interface LightweightChartProps {
    ticker: string;
    date: string;
    timeframe: string;
}

const LightweightChart: React.FC<LightweightChartProps> = ({ ticker, date, timeframe }) => {
    const chartContainerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!chartContainerRef.current) return;


        // Create chart
        const chart = createChart(chartContainerRef.current, {
            crosshair: {
                mode: 0, // 0 for tracking price on both series, can change this if needed
            },
            height: 400,
            layout: {
                background: { color: "#1E1E1E" }, // Dark background
                textColor: "#FFFFFF", // White text
            },
            grid: {
                vertLines: { color: "#2C2C2C" }, // Dark gray vertical grid
                horzLines: { color: "#2C2C2C" }, // Dark gray horizontal grid
            },
        });
        const vwapSeries = chart.addSeries(LineSeries, {
            color: '#FF0000',
            lineWidth: 1,
            // disabling built-in price lines
            lastValueVisible: false,
            priceLineVisible: false,
        });
        const ema9Series = chart.addSeries(LineSeries, {
            color: '#00FFFF',
            lineWidth: 1,
            // disabling built-in price lines
            lastValueVisible: false,
            priceLineVisible: false,
        });

        const candlestickSeries = chart.addSeries(CandlestickSeries, {
            upColor: "#26a69a",
            downColor: "#ef5350",
            borderVisible: false,
            wickUpColor: "#26a69a",
            wickDownColor: "#ef5350",
        });

        const volumeSeries = chart.addSeries(
            HistogramSeries,
            {
                priceFormat: {
                    type: 'volume',
                },
                color: 'blue', // Set the color to blue for the volume bars
            },
            1 // Pane index
        );
        // Moving the series to a different pane
        volumeSeries.moveToPane(2);
        chart.timeScale().applyOptions({
            timeVisible: true, // Enables timestamp visibility
            secondsVisible: true, // Shows seconds in x-axis if available
        });
        const fetchChartData = async () => {
            try {
                const response = await fetch(
                    `http://localhost:8080/api/chart-data?ticker=${ticker}&date=${date}&timeframe=${timeframe}`
                );
                const data = await response.json();
                console.log(data)
                
                if (data?.ohlcData) {
                    // Ensure timestamps are UTC-based and not shifted
                    const parseTimeToUTC = (timeString: string) => {
                        const dateTimeUTC = new Date(`${date}T${timeString}Z`); // Force UTC
                        return Math.floor(dateTimeUTC.getTime() / 1000);
                    };

                    const candlestickData = data.ohlcData.map((item: { Time: string; Open: number; High: number; Low: number; Close: number; }) => ({
                        time: parseTimeToUTC(item.Time),
                        open: item.Open,
                        high: item.High,
                        low: item.Low,
                        close: item.Close,
                    }));

                    const volumeData = data.ohlcData.map((item: { Time: string; Volume: number; }) => ({
                        time: parseTimeToUTC(item.Time),
                        value: item.Volume,
                    }));

                    const vwapData = data.ohlcData.map((item: { Time: string; VWAP: number; }) => ({
                        time: parseTimeToUTC(item.Time),
                        value: item.VWAP,
                    }));
                    const ema9Data = data.ohlcData.map((item: { Time: string; EMA9: number; }) => ({
                        time: parseTimeToUTC(item.Time),
                        value: item.EMA9,
                    }));
                    candlestickSeries.setData(candlestickData);
                    volumeSeries.setData(volumeData);
                    vwapSeries.setData(vwapData);
                    ema9Series.setData(ema9Data);
                    chart.timeScale().fitContent();
                }
            } catch (error) {
                console.error("Error fetching chart data:", error);
            }
        };

        fetchChartData();

        return () => {
            chart.remove();
        };
    }, [ticker, date, timeframe]);

    return (
        <div className="p-4 border rounded-lg shadow-lg max-w-2xl ml-0 bg-white">
            {/* Title */}
            <h2 className="text-xl font-bold mb-2">Market Data Chart</h2>

            {/* Header Section */}
            <div >
                <span>Ticker: {ticker} | </span>
                <span>Date: {date} | </span>
                <span>Timeframe: {timeframe}</span>
            </div>

            {/* Chart Container */}
            <div ref={chartContainerRef} className="w-full bg-white shadow-lg rounded-lg" />
        </div>
    );
};

export default LightweightChart;
