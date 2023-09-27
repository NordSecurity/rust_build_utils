// swift-tools-version: 5.7
// The swift-tools-version declares the minimum version of Swift required to build this package.

import PackageDescription

let package = Package(
    name: "CiHelperScriptsSwift",
    platforms: [
        .iOS(.v13),
        .macOS(.v10_15)
    ],
    products: [
        .library(
            name: "CiHelperScriptsSwift",
            targets: ["CiHelperScriptsSwift", "CciHelperScripts"]),
    ],
    targets: [
        .target(
            name: "CiHelperScriptsSwift",
            dependencies: [
                "CciHelperScripts"
            ],
            path: "Sources"
            ),
        .binaryTarget(
            name: "CciHelperScripts",
            url: "$XCFRAMEWORK_URL",
            checksum: "$XCFRAMEWORK_CHECKSUM"
        )
    ]
)
