// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "PlexCuratorMac",
    platforms: [.macOS(.v12)],
    products: [.executable(name: "PlexCuratorMac", targets: ["PlexCuratorMac"])],
    targets: [.executableTarget(name: "PlexCuratorMac")]
)
