import Foundation

enum DistributionChannel: String {
    case direct
    case appStore
}

struct BuildFlavor {
    let channel: DistributionChannel
    let displayName: String
    let supportsExternalInstaller: Bool
    let supportsLaunchAgentManagement: Bool
    let supportsExternalLogFiles: Bool
    let usesAppSandbox: Bool
    let apiPort: Int

    static let current: BuildFlavor = {
#if APP_STORE
        return BuildFlavor(
            channel: .appStore,
            displayName: "Mac App Store",
            supportsExternalInstaller: false,
            supportsLaunchAgentManagement: false,
            supportsExternalLogFiles: false,
            usesAppSandbox: true,
            apiPort: 8766
        )
#else
        return BuildFlavor(
            channel: .direct,
            displayName: "Direct Download",
            supportsExternalInstaller: true,
            supportsLaunchAgentManagement: true,
            supportsExternalLogFiles: true,
            usesAppSandbox: false,
            apiPort: 8765
        )
#endif
    }()

    var isAppStore: Bool {
        channel == .appStore
    }

    var apiAddress: String {
        "http://127.0.0.1:\(apiPort)"
    }

    var onboardingDescription: String {
        switch channel {
        case .direct:
            return "The installer has already set up the local API, background service, automation manager, and 30-day log retention. The only thing left is connecting Plex Curator to your Plex server."
        case .appStore:
            return "This Mac App Store build keeps all components inside the app sandbox. Connect Plex Curator to your Plex server to finish setup."
        }
    }

    var tokenStorageDescription: String {
        switch channel {
        case .direct:
            return "The token is written to ~/.config/plex-curator/.env with private file permissions and is never displayed back in the app."
        case .appStore:
            return "The token will be stored inside Plex Curator's App Sandbox container and is never displayed back in the app."
        }
    }

    var stateStorageDescription: String {
        switch channel {
        case .direct:
            return "~/.config/plex-curator/"
        case .appStore:
            return "App Sandbox container / Application Support / Plex Curator"
        }
    }

    var automationUnavailableMessage: String {
        "The Mac App Store edition does not install external LaunchAgents. Background services for this edition will use Apple-approved bundled service APIs."
    }
}
