#!/usr/bin/env swift
import AppKit
import Foundation

let args = CommandLine.arguments
guard args.count >= 2 else {
    fputs("usage: generate-app-icon.swift <output.png>\n", stderr)
    exit(2)
}
let outputURL = URL(fileURLWithPath: args[1])
let size = NSSize(width: 1024, height: 1024)
let image = NSImage(size: size)

func roundedRect(_ rect: NSRect, radius: CGFloat) -> NSBezierPath {
    NSBezierPath(roundedRect: rect, xRadius: radius, yRadius: radius)
}

func circle(_ x: CGFloat, _ y: CGFloat, _ d: CGFloat) -> NSBezierPath {
    NSBezierPath(ovalIn: NSRect(x: x, y: y, width: d, height: d))
}

image.lockFocus()

let full = NSRect(origin: .zero, size: size)
NSColor(calibratedRed: 0.035, green: 0.055, blue: 0.082, alpha: 1).setFill()
roundedRect(full.insetBy(dx: 42, dy: 42), radius: 220).fill()

let bgGradient = NSGradient(colors: [
    NSColor(calibratedRed: 0.11, green: 0.15, blue: 0.21, alpha: 1),
    NSColor(calibratedRed: 0.025, green: 0.04, blue: 0.065, alpha: 1)
])!
bgGradient.draw(in: roundedRect(full.insetBy(dx: 58, dy: 58), radius: 205), angle: -55)

NSGraphicsContext.current?.saveGraphicsState()
let shadow = NSShadow()
shadow.shadowColor = NSColor.black.withAlphaComponent(0.45)
shadow.shadowBlurRadius = 36
shadow.shadowOffset = NSSize(width: 0, height: -18)
shadow.set()

let reelRect = NSRect(x: 220, y: 295, width: 515, height: 515)
let reel = NSBezierPath(ovalIn: reelRect)
let metal = NSGradient(colors: [
    NSColor(calibratedWhite: 0.98, alpha: 1),
    NSColor(calibratedWhite: 0.58, alpha: 1),
    NSColor(calibratedWhite: 0.92, alpha: 1),
    NSColor(calibratedWhite: 0.35, alpha: 1)
])!
metal.draw(in: reel, angle: 35)
NSColor(calibratedWhite: 0.12, alpha: 1).setStroke()
reel.lineWidth = 8
reel.stroke()

let hub = circle(428, 503, 98)
NSColor(calibratedWhite: 0.13, alpha: 1).setFill()
hub.fill()

let holes: [(CGFloat,CGFloat,CGFloat)] = [
    (342, 635, 115), (525, 648, 112),
    (610, 492, 112), (500, 350, 110),
    (310, 390, 110)
]
for (x,y,d) in holes {
    let h = circle(x, y, d)
    NSColor(calibratedWhite: 0.08, alpha: 1).setFill()
    h.fill()
    NSColor(calibratedWhite: 0.72, alpha: 0.6).setStroke()
    h.lineWidth = 4
    h.stroke()
}
NSGraphicsContext.current?.restoreGraphicsState()

let strip = NSBezierPath()
strip.move(to: NSPoint(x: 255, y: 330))
strip.curve(to: NSPoint(x: 445, y: 270),
            controlPoint1: NSPoint(x: 320, y: 260),
            controlPoint2: NSPoint(x: 385, y: 245))
strip.curve(to: NSPoint(x: 765, y: 420),
            controlPoint1: NSPoint(x: 560, y: 315),
            controlPoint2: NSPoint(x: 705, y: 360))
strip.curve(to: NSPoint(x: 820, y: 600),
            controlPoint1: NSPoint(x: 805, y: 468),
            controlPoint2: NSPoint(x: 834, y: 545))
strip.curve(to: NSPoint(x: 690, y: 690),
            controlPoint1: NSPoint(x: 810, y: 650),
            controlPoint2: NSPoint(x: 755, y: 694))
strip.curve(to: NSPoint(x: 390, y: 555),
            controlPoint1: NSPoint(x: 565, y: 670),
            controlPoint2: NSPoint(x: 455, y: 605))
strip.curve(to: NSPoint(x: 255, y: 330),
            controlPoint1: NSPoint(x: 300, y: 490),
            controlPoint2: NSPoint(x: 255, y: 405))
strip.close()

let amber = NSGradient(colors: [
    NSColor(calibratedRed: 1.0, green: 0.70, blue: 0.12, alpha: 1),
    NSColor(calibratedRed: 0.98, green: 0.39, blue: 0.04, alpha: 1),
    NSColor(calibratedRed: 0.72, green: 0.19, blue: 0.015, alpha: 1)
])!
amber.draw(in: strip, angle: -20)
NSColor(calibratedRed: 0.27, green: 0.09, blue: 0.01, alpha: 0.85).setStroke()
strip.lineWidth = 7
strip.stroke()

let sprocketColor = NSColor(calibratedRed: 0.12, green: 0.06, blue: 0.02, alpha: 0.9)
sprocketColor.setFill()
for i in 0..<12 {
    let x = 300 + CGFloat(i) * 40
    roundedRect(NSRect(x: x, y: 338 + CGFloat(i % 3) * 7, width: 24, height: 34), radius: 5).fill()
}
for i in 0..<10 {
    let x = 440 + CGFloat(i) * 36
    roundedRect(NSRect(x: x, y: 606 + CGFloat(i % 2) * 8, width: 22, height: 30), radius: 5).fill()
}

let play = NSBezierPath()
play.move(to: NSPoint(x: 485, y: 440))
play.line(to: NSPoint(x: 485, y: 575))
play.line(to: NSPoint(x: 610, y: 507))
play.close()
NSColor(calibratedRed: 1.0, green: 0.72, blue: 0.20, alpha: 0.95).setFill()
play.fill()

image.unlockFocus()

guard
    let tiff = image.tiffRepresentation,
    let bitmap = NSBitmapImageRep(data: tiff),
    let png = bitmap.representation(using: .png, properties: [:])
else {
    fputs("failed to encode icon PNG\n", stderr)
    exit(1)
}

try FileManager.default.createDirectory(
    at: outputURL.deletingLastPathComponent(),
    withIntermediateDirectories: true
)
try png.write(to: outputURL)
print("Generated \(outputURL.path)")
