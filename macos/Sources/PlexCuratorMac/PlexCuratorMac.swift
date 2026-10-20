import SwiftUI
import AppKit
import Foundation
import UserNotifications
import Vision

// MARK: - API Models

struct LibraryInfo: Codable, Identifiable {
    var id: String { "\(name)-\(type)" }
    let name: String
    let type: String
}

struct PlexStatus: Codable {
    let connected: Bool
    let serverName: String?
    let serverVersion: String?
    let libraries: [LibraryInfo]
    let error: String?
}

struct StatusResponse: Codable {
    let apiVersion: String
    let curatorVersion: String
    let plex: PlexStatus
    let stationCount: Int
    let enabledStationCount: Int
}

struct InterstitialPool: Codable, Hashable, Identifiable {
    var id: String { playlist }
    let playlist: String
    let type: String
    let weight: Int
}

struct InterstitialBreakRule: Codable, Hashable {
    let after: Int
    let sequence: [String]
}

struct Station: Codable, Identifiable, Hashable {
    let id: String
    let name: String
    let description: String?
    let enabled: Bool
    let playlist: String
    let preset: String
    let yearMin: Int?
    let yearMax: Int?
    let kidsOnly: Bool
    let adult: Bool
    let perShow: Int
    let total: Int
    let avoidRecent: Int
    let minShowGap: Int
    let seasonal: String
    let specialEvery: Int
    let interstitialPlaylists: [String]
    let interstitialPools: [InterstitialPool]
    let interstitialSequence: [String]?
    let interstitialBreakPattern: [InterstitialBreakRule]?
    let interstitialEvery: Int
    let interstitialCount: Int
    let runtimeBlockMinutes: Int
    let runtimeBlockCount: Int
    let unwatched: Bool
    let syncWatchProgress: Bool
    let includeShows: [String]
    let excludeShows: [String]
}

struct StationsResponse: Codable { let stations: [Station] }

struct StationCreateRequest: Encodable {
    let stationId: String
    let name: String?
    let description: String?
    let playlist: String?
    let preset: String
    let enabled: Bool
    let adult: Bool
}

struct StationCloneRequest: Encodable {
    let newStationId: String
    let name: String?
    let playlist: String?
    let enabled: Bool
}

struct StationMutationResponse: Codable {
    let ok: Bool
    let station: Station
}

struct StationDeleteResponse: Codable {
    let ok: Bool
    let stationId: String
    let backup: String?
    let plexPlaylistPreserved: Bool?
    let historyPreserved: Bool?
}

struct PlaylistSummary: Codable, Identifiable, Hashable {
    var id: String { ratingKey.isEmpty ? title : ratingKey }
    let title: String
    let itemCount: Int?
    let ratingKey: String
    let playlistType: String?
    let smart: Bool
    let updatedAt: String?
}

struct PlaylistsResponse: Codable {
    let playlists: [PlaylistSummary]
}

struct PlaylistDetailResponse: Codable {
    let title: String
    let ratingKey: String
    let playlistType: String?
    let smart: Bool
    let itemCount: Int
    let items: [MediaItem]
}

struct MovieFilterRequest: Encodable {
    let library: String
    let genre: String?
    let yearMin: Int?
    let yearMax: Int?
    let maxRuntime: Int?
    let contentRatings: [String]
    let minAudience: Double?
    let minCritic: Double?
    let watched: Bool
    let unwatched: Bool
    let random: Bool
    let limit: Int?
}

struct MoviePlaylistRequest: Encodable {
    let library: String
    let genre: String?
    let yearMin: Int?
    let yearMax: Int?
    let maxRuntime: Int?
    let contentRatings: [String]
    let minAudience: Double?
    let minCritic: Double?
    let watched: Bool
    let unwatched: Bool
    let random: Bool
    let limit: Int?
    let playlist: String
    let replace: Bool
}

struct MoviePreviewResponse: Codable {
    let count: Int
    let items: [MediaItem]
    let readOnly: Bool
}

struct MoviePlaylistResponse: Codable {
    let ok: Bool
    let playlist: String
    let itemCount: Int
}

struct WishlistEntry: Codable, Identifiable {
    var id: String { "\(requestedTitle)-\(requestedYear ?? 0)" }
    let requestedTitle: String
    let requestedYear: Int?
    let found: Bool
    let matchedTitle: String?
    let item: MediaItem?
}

struct WishlistResponse: Codable {
    let foundCount: Int
    let missingCount: Int
    let totalCount: Int
    let entries: [WishlistEntry]
}

struct ScheduleBlockDefinition: Codable, Identifiable, Hashable {
    var id: Int { index }
    let index: Int
    let name: String
    let type: String?
    let preset: String?
    let minutes: Int
    let seasonal: String?
}

struct ScheduleSummary: Codable, Identifiable, Hashable {
    let id: String
    let description: String
    let playlist: String
    let totalMinutes: Int
    let blocks: [ScheduleBlockDefinition]
}

struct SchedulesResponse: Codable {
    let schedules: [ScheduleSummary]
}

struct ScheduleOptionsRequest: Encodable {
    let playlist: String?
    let avoidRecent: Int
    let minShowGap: Int
    let seasonal: String
    let specialEvery: Int
    let unwatched: Bool
    let ignoreWatchProgress: Bool
}

struct ScheduleBuildRequest: Encodable {
    let playlist: String?
    let avoidRecent: Int
    let minShowGap: Int
    let seasonal: String
    let specialEvery: Int
    let unwatched: Bool
    let ignoreWatchProgress: Bool
    let replace: Bool
}

struct ScheduleBlockPreview: Codable, Identifiable {
    var id: Int { index }
    let index: Int
    let name: String
    let type: String?
    let preset: String?
    let minutes: Int
    let seasonalMode: String?
    let itemCount: Int
    let items: [MediaItem]
}

struct SchedulePreviewResponse: Codable {
    let schedule: ScheduleSummary
    let playlist: String
    let itemCount: Int
    let blocks: [ScheduleBlockPreview]
    let items: [MediaItem]
    let readOnly: Bool
}

struct ScheduleBuildResponse: Codable {
    let ok: Bool
    let schedule: ScheduleSummary
    let playlist: String
    let itemCount: Int
    let blocks: [ScheduleBlockPreview]
}

struct MediaItem: Codable, Identifiable {
    var id: String { ratingKey.isEmpty ? "\(position ?? 0)-\(title ?? "")" : ratingKey }
    let ratingKey: String
    let type: String?
    let title: String?
    let year: Int?
    let contentRating: String?
    let viewCount: Int?
    let watched: Bool
    let position: Int?
    let showTitle: String?
    let seasonNumber: Int?
    let episodeNumber: Int?
    let summary: String?
    let durationMinutes: Int?
    let thumbAvailable: Bool?
    let artworkUrl: String?

    var displayTitle: String {
        if type == "episode" {
            return "\(showTitle ?? "Unknown") — S\(String(format: "%02d", seasonNumber ?? 0))E\(String(format: "%02d", episodeNumber ?? 0)) — \(title ?? "")"
        }
        return year.map { "\(title ?? "Untitled") (\($0))" } ?? (title ?? "Untitled")
    }
}

struct RuntimeBlockSummary: Codable, Identifiable {
    var id: Int { index }
    let index: Int
    let targetMinutes: Int
    let durationMinutes: Double
    let deltaMinutes: Double
    let itemCount: Int
    let startPosition: Int
    let endPosition: Int
    let complete: Bool
    let unknownDurationCount: Int
}

struct PreviewResponse: Codable {
    let station: Station
    let showCount: Int
    let seasonalMode: String
    let itemCount: Int
    let runtimeBlocks: [RuntimeBlockSummary]?
    let items: [MediaItem]
}

struct StationDiff: Codable {
    let currentCount: Int
    let proposedCount: Int
    let keepCount: Int
    let addCount: Int
    let removeCount: Int
    let movedCount: Int
    let added: [String]
    let removed: [String]
}

struct DiffResponse: Codable {
    let station: Station
    let diff: StationDiff
}

struct DoctorCheck: Codable, Identifiable {
    var id: String { "\(status)-\(label)-\(detail)" }
    let status: String
    let label: String
    let detail: String
}

struct DoctorResponse: Codable {
    let result: String
    let failures: Int
    let warnings: Int
    let checks: [DoctorCheck]
}

struct HistoryItem: Codable, Identifiable {
    var id: String { "\(selectedAt)-\(channelName)-\(showTitle)-\(seasonNumber)-\(episodeNumber)" }
    let selectedAt: String
    let showTitle: String
    let seasonNumber: Int
    let episodeNumber: Int
    let episodeTitle: String
    let channelName: String

    var displayDate: String {
        let isoFractional = ISO8601DateFormatter()
        isoFractional.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        let isoBasic = ISO8601DateFormatter()
        isoBasic.formatOptions = [.withInternetDateTime]

        guard let date = isoFractional.date(from: selectedAt) ?? isoBasic.date(from: selectedAt) else {
            return selectedAt.replacingOccurrences(of: "T", with: " ")
        }

        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.timeStyle = .short
        return formatter.string(from: date)
    }
}

struct HistoryResponse: Codable { let history: [HistoryItem] }

struct LogResponse: Codable {
    let job: String
    let errors: Bool
    let path: String
    let lines: [String]
}

struct AutomationJob: Codable, Identifiable, Hashable {
    var id: String { name }
    let name: String
    let label: String
    let description: String
    let loaded: Bool
    let plistExists: Bool
    let state: String?
    let lastExitCode: Int?
    let runs: Int?
    let keepAlive: Bool
    let protected: Bool
}

struct AutomationJobsResponse: Codable {
    let jobs: [AutomationJob]
}

struct AutomationActionResponse: Codable {
    let ok: Bool
    let job: AutomationJob
}

struct MediaOrganizerPreset: Codable, Identifiable, Hashable {
    let id: String
    let name: String
    let description: String
    let excludePatterns: [String]
}

struct MediaOrganizerPresetsResponse: Codable {
    let presets: [MediaOrganizerPreset]
}

struct MediaOrganizerPresetRequest: Encodable {
    let name: String
    let description: String
    let excludePatterns: [String]
}

struct MediaOrganizerPresetMutationResponse: Codable {
    let ok: Bool
    let preset: MediaOrganizerPreset
}

struct MediaOrganizerScanJob: Codable, Identifiable {
    let id: String
    let status: String
    let phase: String
    let current: Int
    let total: Int?
    let discoveredCount: Int
    let processedCount: Int
    let totalCount: Int?
    let excludedCount: Int
    let detail: String?
    let cancelRequested: Bool
    let createdAt: String
    let startedAt: String?
    let updatedAt: String
    let elapsedSeconds: Double
    let result: MediaOrganizerResponse?
    let error: String?

    var isActive: Bool {
        ["queued", "running", "cancelling"].contains(status)
    }
}

struct MediaOrganizerRequest: Encodable {
    let path: String
    let destination: String?
    let recursive: Bool
    let excludePatterns: [String]
}

struct MediaOrganizerAnalyzeRequest: Encodable {
    let source: String
    let destination: String?
}

struct MediaOrganizerOverrideRequest: Encodable {
    let source: String
    let title: String
    let type: String
}

struct MediaOrganizerApplyRequest: Encodable {
    let path: String
    let destination: String?
    let recursive: Bool
    let excludePatterns: [String]
    let includeLowConfidence: Bool
    let deleteExcluded: Bool
    let overrides: [MediaOrganizerOverrideRequest]
}

struct MediaOrganizerReviewFrame: Codable, Hashable, Identifiable {
    var id: String { frameId }
    let frameId: String
    let position: Double
    let timestampSeconds: Double

    enum CodingKeys: String, CodingKey {
        case frameId = "id"
        case position
        case timestampSeconds
    }
}

struct MediaOrganizerItem: Codable, Identifiable, Hashable {
    var id: String { source }
    let source: String
    let target: String
    let originalName: String
    let proposedName: String
    let title: String
    let type: String
    let folder: String
    let confidence: String
    let titleSource: String
    let metadataTitle: String?
    let reviewed: Bool?
    let reviewFrameStatus: String?
    let reviewFrames: [MediaOrganizerReviewFrame]?
    let action: String
}

struct MediaOrganizerExcludedItem: Codable, Identifiable, Hashable {
    var id: String { source }
    let source: String
    let originalName: String
    let relativePath: String
    let matchedPattern: String
}

struct MediaOrganizerResponse: Codable {
    let root: String
    let destination: String
    let recursive: Bool
    let totalFound: Int?
    let count: Int
    let excludedCount: Int?
    let reviewCount: Int
    let excludePatterns: [String]?
    let excludedItems: [MediaOrganizerExcludedItem]?
    let items: [MediaOrganizerItem]
    let appliedCount: Int?
    let skippedCount: Int?
    let deletedExcludedCount: Int?
    let errorCount: Int?
    let manifest: String?
}

struct APIErrorResponse: Codable { let detail: String }
struct PreviewRequest: Codable { let total: Int? }
struct RefreshRequest: Codable { let total: Int?; let dryRun: Bool; let force: Bool }

struct StationUpdateRequest: Encodable {
    let name: String
    let description: String
    let enabled: Bool
    let playlist: String
    let preset: String
    let yearMin: Int?
    let yearMax: Int?
    let kidsOnly: Bool
    let adult: Bool
    let perShow: Int
    let total: Int
    let avoidRecent: Int
    let minShowGap: Int
    let seasonal: String
    let specialEvery: Int
    let interstitialPlaylists: [String]
    let interstitialPools: [InterstitialPool]
    let interstitialSequence: [String]
    let interstitialBreakPattern: [InterstitialBreakRule]
    let interstitialEvery: Int
    let interstitialCount: Int
    let runtimeBlockMinutes: Int
    let runtimeBlockCount: Int
    let unwatched: Bool
    let syncWatchProgress: Bool
    let includeShows: [String]
    let excludeShows: [String]

    enum CodingKeys: String, CodingKey {
        case name, description, enabled, playlist, preset
        case yearMin, yearMax, kidsOnly, adult, perShow, total
        case avoidRecent, minShowGap, seasonal, specialEvery
        case interstitialPlaylists, interstitialPools, interstitialSequence, interstitialBreakPattern, interstitialEvery, interstitialCount
        case runtimeBlockMinutes, runtimeBlockCount
        case unwatched, syncWatchProgress, includeShows, excludeShows
    }

    func encode(to encoder: Encoder) throws {
        var c = encoder.container(keyedBy: CodingKeys.self)
        try c.encode(name, forKey: .name)
        try c.encode(description, forKey: .description)
        try c.encode(enabled, forKey: .enabled)
        try c.encode(playlist, forKey: .playlist)
        try c.encode(preset, forKey: .preset)
        if let yearMin { try c.encode(yearMin, forKey: .yearMin) } else { try c.encodeNil(forKey: .yearMin) }
        if let yearMax { try c.encode(yearMax, forKey: .yearMax) } else { try c.encodeNil(forKey: .yearMax) }
        try c.encode(kidsOnly, forKey: .kidsOnly)
        try c.encode(adult, forKey: .adult)
        try c.encode(perShow, forKey: .perShow)
        try c.encode(total, forKey: .total)
        try c.encode(avoidRecent, forKey: .avoidRecent)
        try c.encode(minShowGap, forKey: .minShowGap)
        try c.encode(seasonal, forKey: .seasonal)
        try c.encode(specialEvery, forKey: .specialEvery)
        try c.encode(interstitialPlaylists, forKey: .interstitialPlaylists)
        try c.encode(interstitialPools, forKey: .interstitialPools)
        try c.encode(interstitialSequence, forKey: .interstitialSequence)
        try c.encode(interstitialBreakPattern, forKey: .interstitialBreakPattern)
        try c.encode(interstitialEvery, forKey: .interstitialEvery)
        try c.encode(interstitialCount, forKey: .interstitialCount)
        try c.encode(runtimeBlockMinutes, forKey: .runtimeBlockMinutes)
        try c.encode(runtimeBlockCount, forKey: .runtimeBlockCount)
        try c.encode(unwatched, forKey: .unwatched)
        try c.encode(syncWatchProgress, forKey: .syncWatchProgress)
        try c.encode(includeShows, forKey: .includeShows)
        try c.encode(excludeShows, forKey: .excludeShows)
    }
}

struct StationUpdateResponse: Codable {
    let ok: Bool
    let station: Station
}

struct RefreshResponse: Codable {
    let ok: Bool
    let dryRun: Bool
    let stationId: String?
    let playlist: String?
    let itemCount: Int?
}

// MARK: - API Client

enum APIClientError: LocalizedError {
    case missingKey(String)
    case server(Int, String)
    case invalidResponse
    case transport(String)

    var errorDescription: String? {
        switch self {
        case .missingKey(let path): return "API key missing at \(path). Start the v12 API once or run ./plex-curator-api key."
        case .server(let code, let message): return "API \(code): \(message)"
        case .invalidResponse: return "Invalid API response."
        case .transport(let message): return message
        }
    }
}

final class APIClient {
    let baseURL = URL(string: "http://127.0.0.1:8765")!

    private var decoder: JSONDecoder {
        let d = JSONDecoder()
        d.keyDecodingStrategy = .convertFromSnakeCase
        return d
    }

    private var encoder: JSONEncoder {
        let e = JSONEncoder()
        e.keyEncodingStrategy = .convertToSnakeCase
        return e
    }

    var apiKeyPath: String {
        FileManager.default.homeDirectoryForCurrentUser
            .appendingPathComponent(".config/plex-curator/api.key").path
    }

    private func apiKey() throws -> String {
        guard let key = try? String(contentsOfFile: apiKeyPath, encoding: .utf8)
            .trimmingCharacters(in: .whitespacesAndNewlines), !key.isEmpty else {
            throw APIClientError.missingKey(apiKeyPath)
        }
        return key
    }

    private func request<T: Decodable>(
        _ path: String,
        method: String = "GET",
        body: Data? = nil,
        authenticated: Bool = false,
        timeout: TimeInterval = 30
    ) async throws -> T {
        guard let url = URL(string: path, relativeTo: baseURL) else {
            throw APIClientError.invalidResponse
        }
        var req = URLRequest(url: url)
        req.httpMethod = method
        req.timeoutInterval = timeout
        req.setValue("application/json", forHTTPHeaderField: "Accept")
        if let body {
            req.httpBody = body
            req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        }
        if authenticated {
            req.setValue(try apiKey(), forHTTPHeaderField: "X-Plex-Curator-Key")
        }

        do {
            let (data, response) = try await URLSession.shared.data(for: req)
            guard let http = response as? HTTPURLResponse else { throw APIClientError.invalidResponse }
            guard (200..<300).contains(http.statusCode) else {
                let detail = (try? decoder.decode(APIErrorResponse.self, from: data).detail)
                    ?? String(data: data, encoding: .utf8) ?? "Unknown error"
                throw APIClientError.server(http.statusCode, detail)
            }
            return try decoder.decode(T.self, from: data)
        } catch let e as APIClientError {
            throw e
        } catch {
            throw APIClientError.transport(error.localizedDescription)
        }
    }

    func status() async throws -> StatusResponse {
        try await request("/api/v1/status")
    }

    func stations() async throws -> [Station] {
        let r: StationsResponse = try await request("/api/v1/stations")
        return r.stations
    }

    func doctor() async throws -> DoctorResponse {
        try await request("/api/v1/doctor")
    }

    func preview(_ id: String) async throws -> PreviewResponse {
        let body = try encoder.encode(PreviewRequest(total: nil))
        return try await request("/api/v1/stations/\(id)/preview", method: "POST", body: body)
    }

    func diff(_ id: String) async throws -> DiffResponse {
        try await request("/api/v1/stations/\(id)/diff")
    }

    func refresh(_ id: String, dryRun: Bool) async throws -> RefreshResponse {
        let body = try encoder.encode(RefreshRequest(total: nil, dryRun: dryRun, force: false))
        return try await request(
            "/api/v1/stations/\(id)/refresh",
            method: "POST",
            body: body,
            authenticated: true
        )
    }

    func createStation(_ value: StationCreateRequest) async throws -> Station {
        let body = try encoder.encode(value)
        let response: StationMutationResponse = try await request(
            "/api/v1/stations",
            method: "POST",
            body: body,
            authenticated: true
        )
        return response.station
    }

    func updateStation(_ id: String, request update: StationUpdateRequest) async throws -> Station {
        let body = try encoder.encode(update)
        let response: StationUpdateResponse = try await request(
            "/api/v1/stations/\(id)",
            method: "PUT",
            body: body,
            authenticated: true
        )
        return response.station
    }

    func cloneStation(_ id: String, request value: StationCloneRequest) async throws -> Station {
        let body = try encoder.encode(value)
        let response: StationMutationResponse = try await request(
            "/api/v1/stations/\(id)/clone",
            method: "POST",
            body: body,
            authenticated: true
        )
        return response.station
    }

    func deleteStation(_ id: String) async throws -> StationDeleteResponse {
        try await request(
            "/api/v1/stations/\(id)",
            method: "DELETE",
            authenticated: true
        )
    }

    func playlists() async throws -> [PlaylistSummary] {
        let response: PlaylistsResponse = try await request("/api/v1/playlists")
        return response.playlists
    }

    func playlistDetail(name: String) async throws -> PlaylistDetailResponse {
        var components = URLComponents()
        components.path = "/api/v1/playlist"
        components.queryItems = [URLQueryItem(name: "name", value: name)]
        return try await request(components.string ?? "/api/v1/playlist")
    }

    func artworkURL(ratingKey: String, width: Int = 240, height: Int = 360) -> URL? {
        guard !ratingKey.isEmpty else { return nil }
        var components = URLComponents(
            url: baseURL
                .appendingPathComponent("api")
                .appendingPathComponent("v1")
                .appendingPathComponent("artwork")
                .appendingPathComponent(ratingKey),
            resolvingAgainstBaseURL: false
        )
        components?.queryItems = [
            URLQueryItem(name: "width", value: String(width)),
            URLQueryItem(name: "height", value: String(height))
        ]
        return components?.url
    }

    func schedules() async throws -> [ScheduleSummary] {
        let response: SchedulesResponse = try await request("/api/v1/schedules")
        return response.schedules
    }

    func schedulePreview(
        id: String,
        request value: ScheduleOptionsRequest
    ) async throws -> SchedulePreviewResponse {
        let body = try encoder.encode(value)
        return try await request(
            "/api/v1/schedules/\(id)/preview",
            method: "POST",
            body: body
        )
    }

    func buildSchedule(
        id: String,
        request value: ScheduleBuildRequest
    ) async throws -> ScheduleBuildResponse {
        let body = try encoder.encode(value)
        return try await request(
            "/api/v1/schedules/\(id)/build",
            method: "POST",
            body: body,
            authenticated: true
        )
    }

    func moviePreview(_ filter: MovieFilterRequest) async throws -> MoviePreviewResponse {
        let body = try encoder.encode(filter)
        return try await request(
            "/api/v1/movies/preview",
            method: "POST",
            body: body
        )
    }

    func createMoviePlaylist(_ requestValue: MoviePlaylistRequest) async throws -> MoviePlaylistResponse {
        let body = try encoder.encode(requestValue)
        return try await request(
            "/api/v1/movies/playlist",
            method: "POST",
            body: body,
            authenticated: true
        )
    }

    func mediaOrganizerFrameURL(_ frameId: String) -> URL? {
        let parts = frameId.split(separator: "/", omittingEmptySubsequences: true)
        guard parts.count == 2 else { return nil }
        return baseURL
            .appendingPathComponent("api")
            .appendingPathComponent("v1")
            .appendingPathComponent("media-organizer")
            .appendingPathComponent("frame")
            .appendingPathComponent(String(parts[0]))
            .appendingPathComponent(String(parts[1]))
    }

    func kidsScaryWishlist() async throws -> WishlistResponse {
        try await request("/api/v1/wishlist/kids-scary")
    }

    func mediaOrganizerPresets() async throws -> [MediaOrganizerPreset] {
        let response: MediaOrganizerPresetsResponse = try await request(
            "/api/v1/media-organizer/presets"
        )
        return response.presets.sorted {
            $0.name.localizedCaseInsensitiveCompare($1.name) == .orderedAscending
        }
    }

    func createMediaOrganizerPreset(
        name: String,
        description: String,
        excludePatterns: [String]
    ) async throws -> MediaOrganizerPreset {
        let body = try encoder.encode(
            MediaOrganizerPresetRequest(
                name: name,
                description: description,
                excludePatterns: excludePatterns
            )
        )
        let response: MediaOrganizerPresetMutationResponse = try await request(
            "/api/v1/media-organizer/presets",
            method: "POST",
            body: body,
            authenticated: true
        )
        return response.preset
    }

    func updateMediaOrganizerPreset(
        id: String,
        name: String,
        description: String,
        excludePatterns: [String]
    ) async throws -> MediaOrganizerPreset {
        let escaped = id.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? id
        let body = try encoder.encode(
            MediaOrganizerPresetRequest(
                name: name,
                description: description,
                excludePatterns: excludePatterns
            )
        )
        let response: MediaOrganizerPresetMutationResponse = try await request(
            "/api/v1/media-organizer/presets/\(escaped)",
            method: "PUT",
            body: body,
            authenticated: true
        )
        return response.preset
    }

    func deleteMediaOrganizerPreset(id: String) async throws {
        let escaped = id.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? id
        let _: MediaOrganizerPresetMutationResponse = try await request(
            "/api/v1/media-organizer/presets/\(escaped)",
            method: "DELETE",
            authenticated: true
        )
    }

    func startMediaOrganizerScanJob(
        path: String,
        destination: String?,
        recursive: Bool,
        excludePatterns: [String]
    ) async throws -> MediaOrganizerScanJob {
        let body = try encoder.encode(
            MediaOrganizerRequest(
                path: path,
                destination: destination,
                recursive: recursive,
                excludePatterns: excludePatterns
            )
        )
        return try await request(
            "/api/v1/media-organizer/scan-jobs",
            method: "POST",
            body: body
        )
    }

    func mediaOrganizerScanJob(id: String) async throws -> MediaOrganizerScanJob {
        let escaped = id.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? id
        return try await request(
            "/api/v1/media-organizer/scan-jobs/\(escaped)"
        )
    }

    func cancelMediaOrganizerScanJob(id: String) async throws -> MediaOrganizerScanJob {
        let escaped = id.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? id
        return try await request(
            "/api/v1/media-organizer/scan-jobs/\(escaped)/cancel",
            method: "POST",
            authenticated: true
        )
    }

    func scanMediaOrganizer(
        path: String,
        destination: String?,
        recursive: Bool,
        excludePatterns: [String]
    ) async throws -> MediaOrganizerResponse {
        let body = try encoder.encode(
            MediaOrganizerRequest(
                path: path,
                destination: destination,
                recursive: recursive,
                excludePatterns: excludePatterns
            )
        )
        return try await request(
            "/api/v1/media-organizer/scan",
            method: "POST",
            body: body,
            timeout: 300
        )
    }

    func analyzeMediaOrganizerItem(
        source: String,
        destination: String?
    ) async throws -> MediaOrganizerItem {
        let body = try encoder.encode(
            MediaOrganizerAnalyzeRequest(
                source: source,
                destination: destination
            )
        )
        return try await request(
            "/api/v1/media-organizer/analyze",
            method: "POST",
            body: body,
            timeout: 90
        )
    }

    func applyMediaOrganizer(
        path: String,
        destination: String?,
        recursive: Bool,
        includeLowConfidence: Bool,
        deleteExcluded: Bool,
        excludePatterns: [String],
        overrides: [MediaOrganizerOverrideRequest]
    ) async throws -> MediaOrganizerResponse {
        let body = try encoder.encode(
            MediaOrganizerApplyRequest(
                path: path,
                destination: destination,
                recursive: recursive,
                excludePatterns: excludePatterns,
                includeLowConfidence: includeLowConfidence,
                deleteExcluded: deleteExcluded,
                overrides: overrides
            )
        )
        return try await request(
            "/api/v1/media-organizer/apply",
            method: "POST",
            body: body,
            authenticated: true,
            timeout: 300
        )
    }

    func history() async throws -> [HistoryItem] {
        let r: HistoryResponse = try await request("/api/v1/history?limit=150")
        return r.history
    }

    func logs(job: String, errors: Bool) async throws -> LogResponse {
        let escaped = job.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? job
        return try await request("/api/v1/logs/\(escaped)?errors=\(errors ? "true" : "false")&lines=250")
    }

    func automationJobs() async throws -> [AutomationJob] {
        let response: AutomationJobsResponse = try await request("/api/v1/automation")
        return response.jobs
    }

    func automationAction(job: String, action: String) async throws -> AutomationJob {
        let escaped = job.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? job
        let response: AutomationActionResponse = try await request(
            "/api/v1/automation/\(escaped)/\(action)",
            method: "POST",
            authenticated: true
        )
        return response.job
    }
}

struct MediaVisualSuggestion {
    let title: String?
    let type: String?
    let recognizedText: [String]

    var summary: String {
        recognizedText.joined(separator: " • ")
    }
}

enum MediaVisualAnalyzer {
    private static let networkNames: [(needle: String, display: String)] = [
        ("nickelodeon", "Nickelodeon"),
        ("nick at nite", "Nick at Nite"),
        ("cartoon network", "Cartoon Network"),
        ("toon disney", "Toon Disney"),
        ("disney channel", "Disney Channel"),
        ("fox kids", "Fox Kids"),
        ("kids wb", "Kids WB"),
        ("kids' wb", "Kids WB"),
        ("boomerang", "Boomerang"),
        ("adult swim", "Adult Swim"),
        ("comedy central", "Comedy Central"),
        ("pbs kids", "PBS Kids"),
        ("mtv", "MTV"),
        ("vh1", "VH1")
    ]

    static func analyze(frameURLs: [URL]) async -> MediaVisualSuggestion {
        guard !frameURLs.isEmpty else {
            return MediaVisualSuggestion(title: nil, type: nil, recognizedText: [])
        }

        var allText: [String] = []
        for url in frameURLs {
            if let text = await recognizeText(in: url) {
                allText.append(contentsOf: text)
            }
        }

        var seen = Set<String>()
        let unique = allText
            .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }
            .filter { value in
                let key = value.lowercased()
                guard !seen.contains(key) else { return false }
                seen.insert(key)
                return true
            }

        let joined = unique.joined(separator: " ").lowercased()
        let detectedNetwork = networkNames.first { joined.contains($0.needle) }?.display
        let detectedType = inferType(from: joined)
        let phrase = bestPhrase(from: unique, joined: joined)
        let year = extractYear(from: joined)

        var titleParts: [String] = []
        if let detectedNetwork {
            titleParts.append(detectedNetwork)
        }
        if let phrase, !titleParts.contains(where: { $0.caseInsensitiveCompare(phrase) == .orderedSame }) {
            titleParts.append(phrase)
        }
        if let year {
            titleParts.append(year)
        }

        let title = titleParts.isEmpty ? nil : titleParts.joined(separator: " - ")
        return MediaVisualSuggestion(
            title: title,
            type: detectedType,
            recognizedText: Array(unique.prefix(12))
        )
    }

    private static func recognizeText(in url: URL) async -> [String]? {
        do {
            let (data, response) = try await URLSession.shared.data(from: url)
            guard let http = response as? HTTPURLResponse,
                  (200..<300).contains(http.statusCode),
                  let image = NSImage(data: data),
                  let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil)
            else {
                return nil
            }

            return try await Task.detached(priority: .userInitiated) {
                let request = VNRecognizeTextRequest()
                request.recognitionLevel = .accurate
                request.usesLanguageCorrection = true
                request.minimumTextHeight = 0.02

                let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
                try handler.perform([request])

                return (request.results ?? []).compactMap {
                    $0.topCandidates(1).first?.string
                }
            }.value
        } catch {
            return nil
        }
    }

    private static func inferType(from text: String) -> String? {
        let bumperPhrases = [
            "we'll be right back", "well be right back", "be right back",
            "up next", "coming up", "back to"
        ]
        if bumperPhrases.contains(where: { text.contains($0) }) {
            return "bumper"
        }

        let commercialPhrases = [
            "call now", "order now", "limited time", "available now",
            "available at", "save $", "only $", "special offer", "visit www",
            "www.", "while supplies last"
        ]
        if commercialPhrases.contains(where: { text.contains($0) }) {
            return "commercial"
        }

        let promoPhrases = [
            "premieres", "premiere", "tonight", "this saturday", "this sunday",
            "new episode", "all new", "coming this"
        ]
        if promoPhrases.contains(where: { text.contains($0) }) {
            return "promo"
        }

        if networkNames.contains(where: { text.contains($0.needle) }) {
            return "station-id"
        }
        return nil
    }

    private static func bestPhrase(from lines: [String], joined: String) -> String? {
        let canonical: [(needle: String, title: String)] = [
            ("we'll be right back", "We'll Be Right Back"),
            ("well be right back", "We'll Be Right Back"),
            ("up next", "Up Next"),
            ("coming up", "Coming Up"),
            ("back to", "Back To Programming"),
            ("premieres", "Promo"),
            ("premiere", "Promo"),
            ("tonight", "Tonight Promo"),
            ("new episode", "New Episode Promo")
        ]
        if let phrase = canonical.first(where: { joined.contains($0.needle) }) {
            return phrase.title
        }

        let candidates = lines.filter { line in
            let trimmed = line.trimmingCharacters(in: .whitespacesAndNewlines)
            return trimmed.count >= 4 &&
                trimmed.count <= 60 &&
                trimmed.rangeOfCharacter(from: .letters) != nil
        }
        return candidates.first
    }

    private static func extractYear(from text: String) -> String? {
        let pattern = #"\b(19\d{2}|20\d{2})\b"#
        guard let regex = try? NSRegularExpression(pattern: pattern) else { return nil }
        let range = NSRange(text.startIndex..<text.endIndex, in: text)
        guard let match = regex.firstMatch(in: text, range: range),
              let swiftRange = Range(match.range(at: 1), in: text)
        else {
            return nil
        }
        return String(text[swiftRange])
    }
}

final class NotificationManager {
    static let shared = NotificationManager()

    private init() {}

    func send(title: String, body: String) {
        let center = UNUserNotificationCenter.current()
        center.getNotificationSettings { settings in
            switch settings.authorizationStatus {
            case .authorized, .provisional:
                self.schedule(center: center, title: title, body: body)
            case .notDetermined:
                center.requestAuthorization(options: [.alert, .sound]) { granted, _ in
                    if granted {
                        self.schedule(center: center, title: title, body: body)
                    }
                }
            default:
                break
            }
        }
    }

    private func schedule(center: UNUserNotificationCenter, title: String, body: String) {
        let content = UNMutableNotificationContent()
        content.title = title
        content.body = body
        content.sound = .default
        let request = UNNotificationRequest(
            identifier: UUID().uuidString,
            content: content,
            trigger: nil
        )
        center.add(request)
    }
}

// MARK: - App Model

@MainActor
final class AppModel: ObservableObject {
    @Published var status: StatusResponse?
    @Published var stations: [Station] = []
    @Published var doctor: DoctorResponse?
    @Published var history: [HistoryItem] = []
    @Published var preview: PreviewResponse?
    @Published var diff: DiffResponse?
    @Published var log: LogResponse?
    @Published var automationJobs: [AutomationJob] = []
    @Published var playlists: [PlaylistSummary] = []
    @Published var schedules: [ScheduleSummary] = []
    @Published var mediaOrganizer: MediaOrganizerResponse?
    @Published var mediaOrganizerScanJob: MediaOrganizerScanJob?
    @Published var mediaOrganizerScanning = false
    @Published var mediaOrganizerPresets: [MediaOrganizerPreset] = []
    @Published var analyzedMediaItems: [String: MediaOrganizerItem] = [:]
    @Published var error: String?
    @Published var message: String?
    @Published var loading = false

    let api = APIClient()

    func bootstrap() async { await refreshDashboard() }

    func refreshDashboard() async {
        loading = true
        defer { loading = false }
        do {
            async let s = api.status()
            async let st = api.stations()
            async let d = api.doctor()
            status = try await s
            stations = try await st
            doctor = try await d
            error = nil
        } catch {
            status = nil
            self.error = error.localizedDescription
        }
    }

    func loadPreview(_ station: Station) async {
        do { preview = try await api.preview(station.id); error = nil }
        catch { self.error = error.localizedDescription }
    }

    func loadDiff(_ station: Station) async {
        do { diff = try await api.diff(station.id); error = nil }
        catch { self.error = error.localizedDescription }
    }

    func dryRun(_ station: Station) async {
        do {
            _ = try await api.refresh(station.id, dryRun: true)
            message = "Dry run completed. No Plex changes were made."
            diff = try await api.diff(station.id)
            error = nil
        } catch { self.error = error.localizedDescription }
    }

    func refresh(_ station: Station) async {
        do {
            let r = try await api.refresh(station.id, dryRun: false)
            message = "Refreshed \(r.playlist ?? station.name) with \(r.itemCount ?? 0) items."
            NotificationManager.shared.send(
                title: "Plex Curator",
                body: "Refreshed \(r.playlist ?? station.name) with \(r.itemCount ?? 0) items."
            )
            preview = nil
            diff = nil
            await refreshDashboard()
        } catch { self.error = error.localizedDescription }
    }

    func createStation(_ request: StationCreateRequest) async -> Station? {
        do {
            let created = try await api.createStation(request)
            stations.append(created)
            stations.sort {
                $0.name.localizedCaseInsensitiveCompare($1.name) == .orderedAscending
            }
            message = "Created \(created.name)."
            error = nil
            return created
        } catch {
            self.error = error.localizedDescription
            return nil
        }
    }

    func updateStation(_ station: Station, request: StationUpdateRequest) async -> Station? {
        do {
            let updated = try await api.updateStation(station.id, request: request)
            if let index = stations.firstIndex(where: { $0.id == updated.id }) {
                stations[index] = updated
            }
            message = "Saved \(updated.name)."
            error = nil
            return updated
        } catch {
            self.error = error.localizedDescription
            return nil
        }
    }

    func cloneStation(_ station: Station, request: StationCloneRequest) async -> Station? {
        do {
            let created = try await api.cloneStation(station.id, request: request)
            stations.append(created)
            stations.sort {
                $0.name.localizedCaseInsensitiveCompare($1.name) == .orderedAscending
            }
            message = "Duplicated \(station.name) as \(created.name)."
            error = nil
            return created
        } catch {
            self.error = error.localizedDescription
            return nil
        }
    }

    func deleteStation(_ station: Station) async -> Bool {
        do {
            let result = try await api.deleteStation(station.id)
            stations.removeAll { $0.id == station.id }
            preview = nil
            diff = nil
            message = result.backup.map {
                "Deleted \(station.name). Safety backup: \($0)"
            } ?? "Deleted \(station.name). Plex playlist and history were preserved."
            error = nil
            return true
        } catch {
            self.error = error.localizedDescription
            return false
        }
    }

    func loadSchedules() async {
        do {
            schedules = try await api.schedules()
            error = nil
        } catch {
            self.error = error.localizedDescription
        }
    }

    func loadPlaylists() async {
        do {
            playlists = try await api.playlists()
            error = nil
        } catch {
            self.error = error.localizedDescription
        }
    }

    func loadMediaOrganizerPresets() async {
        do {
            mediaOrganizerPresets = try await api.mediaOrganizerPresets()
            error = nil
        } catch {
            self.error = error.localizedDescription
        }
    }

    func saveMediaOrganizerPreset(
        id: String?,
        name: String,
        description: String,
        excludePatterns: [String],
        createNew: Bool = false
    ) async -> MediaOrganizerPreset? {
        do {
            let preset: MediaOrganizerPreset
            if let id, !id.isEmpty, !createNew {
                preset = try await api.updateMediaOrganizerPreset(
                    id: id,
                    name: name,
                    description: description,
                    excludePatterns: excludePatterns
                )
            } else {
                preset = try await api.createMediaOrganizerPreset(
                    name: name,
                    description: description,
                    excludePatterns: excludePatterns
                )
            }
            await loadMediaOrganizerPresets()
            message = "Saved Media Organizer preset \(preset.name)."
            error = nil
            return preset
        } catch {
            self.error = error.localizedDescription
            return nil
        }
    }

    func deleteMediaOrganizerPreset(id: String) async -> Bool {
        do {
            try await api.deleteMediaOrganizerPreset(id: id)
            await loadMediaOrganizerPresets()
            message = "Deleted Media Organizer preset."
            error = nil
            return true
        } catch {
            self.error = error.localizedDescription
            return false
        }
    }

    func scanMediaOrganizer(
        path: String,
        destination: String?,
        recursive: Bool,
        excludePatterns: [String]
    ) async {
        analyzedMediaItems.removeAll()
        mediaOrganizer = nil
        mediaOrganizerScanJob = nil
        mediaOrganizerScanning = true
        defer { mediaOrganizerScanning = false }

        do {
            var job = try await api.startMediaOrganizerScanJob(
                path: path,
                destination: destination,
                recursive: recursive,
                excludePatterns: excludePatterns
            )
            mediaOrganizerScanJob = job
            error = nil

            while job.isActive {
                try await Task.sleep(nanoseconds: 500_000_000)
                job = try await api.mediaOrganizerScanJob(id: job.id)
                mediaOrganizerScanJob = job
            }

            switch job.status {
            case "completed":
                if let result = job.result {
                    mediaOrganizer = result
                    message = "Media scan completed: \(result.totalFound ?? result.count) videos found, \(result.excludedCount ?? 0) excluded."
                    error = nil
                } else {
                    self.error = "Media scan completed without a result."
                }
            case "cancelled":
                message = "Media scan cancelled."
                error = nil
            case "failed":
                self.error = job.error ?? "Media scan failed."
            default:
                break
            }
        } catch is CancellationError {
            message = "Media scan polling stopped."
        } catch {
            self.error = error.localizedDescription
        }
    }

    func cancelMediaOrganizerScan() async {
        guard let job = mediaOrganizerScanJob, job.isActive else { return }
        do {
            mediaOrganizerScanJob = try await api.cancelMediaOrganizerScanJob(id: job.id)
            message = "Media scan cancellation requested."
            error = nil
        } catch {
            self.error = error.localizedDescription
        }
    }

    func analyzeMediaOrganizerItem(
        source: String,
        destination: String?
    ) async -> MediaOrganizerItem? {
        do {
            let item = try await api.analyzeMediaOrganizerItem(
                source: source,
                destination: destination
            )
            analyzedMediaItems[source] = item
            error = nil
            return item
        } catch {
            self.error = error.localizedDescription
            return nil
        }
    }

    func applyMediaOrganizer(
        path: String,
        destination: String?,
        recursive: Bool,
        includeLowConfidence: Bool,
        deleteExcluded: Bool,
        excludePatterns: [String],
        overrides: [MediaOrganizerOverrideRequest]
    ) async -> Bool {
        loading = true
        defer { loading = false }
        do {
            let result = try await api.applyMediaOrganizer(
                path: path,
                destination: destination,
                recursive: recursive,
                includeLowConfidence: includeLowConfidence,
                deleteExcluded: deleteExcluded,
                excludePatterns: excludePatterns,
                overrides: overrides
            )
            mediaOrganizer = result
            let moved = result.appliedCount ?? 0
            let skipped = result.skippedCount ?? 0
            let deleted = result.deletedExcludedCount ?? 0
            message = "Media Organizer moved \(moved) file\(moved == 1 ? "" : "s"); skipped \(skipped); deleted \(deleted) excluded."
            error = nil
            return true
        } catch {
            self.error = error.localizedDescription
            return false
        }
    }

    func loadHistory() async {
        do { history = try await api.history(); error = nil }
        catch { self.error = error.localizedDescription }
    }

    func loadLogs(job: String, errors: Bool) async {
        do { log = try await api.logs(job: job, errors: errors); error = nil }
        catch { self.error = error.localizedDescription }
    }

    func loadAutomation() async {
        do {
            automationJobs = try await api.automationJobs()
            error = nil
        } catch {
            self.error = error.localizedDescription
        }
    }

    func automationAction(_ job: AutomationJob, action: String) async {
        do {
            let updated = try await api.automationAction(job: job.name, action: action)
            if let index = automationJobs.firstIndex(where: { $0.name == updated.name }) {
                automationJobs[index] = updated
            } else {
                automationJobs.append(updated)
            }
            message = "\(job.name): \(action) completed."
            NotificationManager.shared.send(
                title: "Plex Curator Automation",
                body: "\(job.name): \(action) completed."
            )
            error = nil
        } catch {
            self.error = error.localizedDescription
        }
    }
}

// MARK: - App

@main
struct PlexCuratorMacApp: App {
    @StateObject private var model = AppModel()

    var body: some Scene {
        WindowGroup("Plex Curator") {
            RootView()
                .environmentObject(model)
                .frame(minWidth: 980, minHeight: 650)
                .task { await model.bootstrap() }
        }
    }
}

// MARK: - Views

struct RootView: View {
    @EnvironmentObject var model: AppModel

    var body: some View {
        NavigationView {
            List {
                Section("Plex Curator") {
                    NavigationLink(destination: DashboardView()) { Label("Dashboard", systemImage: "gauge") }
                    NavigationLink(destination: StationsView()) { Label("Stations", systemImage: "tv") }
                    NavigationLink(destination: SchedulesView()) { Label("Schedules", systemImage: "calendar") }
                    NavigationLink(destination: PlaylistsView()) { Label("Playlists", systemImage: "rectangle.stack") }
                    NavigationLink(destination: MediaOrganizerView()) { Label("Media Organizer", systemImage: "folder.badge.gearshape") }
                    NavigationLink(destination: MovieCuratorView()) { Label("Movie Curator", systemImage: "film.stack") }
                    NavigationLink(destination: KidsScaryWishlistView()) { Label("Kids Scary Wishlist", systemImage: "checklist") }
                    NavigationLink(destination: HistoryView()) { Label("History", systemImage: "clock.arrow.circlepath") }
                    NavigationLink(destination: HealthView()) { Label("Health", systemImage: "heart.text.square") }
                    NavigationLink(destination: AutomationView()) { Label("Automation", systemImage: "clock.badge.checkmark") }
                    NavigationLink(destination: LogsView()) { Label("Logs", systemImage: "doc.text.magnifyingglass") }
                    NavigationLink(destination: SettingsView()) { Label("Settings", systemImage: "gearshape") }
                }
            }
            .listStyle(SidebarListStyle())
            .frame(minWidth: 210)

            DashboardView()
        }
        .overlay(alignment: .bottom) {
            if let error = model.error {
                notice(icon: "exclamationmark.triangle.fill", text: error) { model.error = nil }
            } else if let message = model.message {
                notice(icon: "checkmark.circle.fill", text: message) { model.message = nil }
            }
        }
    }

    private func notice(icon: String, text: String, dismiss: @escaping () -> Void) -> some View {
        HStack {
            Image(systemName: icon)
            Text(text).lineLimit(2)
            Spacer()
            Button("Dismiss", action: dismiss)
        }
        .padding(10)
        .background(.ultraThickMaterial)
    }
}

struct StatusBadge: View {
    let text: String
    let good: Bool
    var body: some View {
        HStack(spacing: 6) {
            Circle().fill(good ? Color.green : Color.orange).frame(width: 8, height: 8)
            Text(text).font(.caption)
        }
        .padding(.horizontal, 9).padding(.vertical, 5)
        .background(Color.secondary.opacity(0.12)).clipShape(Capsule())
    }
}

struct DashboardView: View {
    @EnvironmentObject var model: AppModel

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {
                HStack {
                    VStack(alignment: .leading) {
                        Text("Plex Curator").font(.largeTitle.bold())
                        Text("Local programming control").foregroundColor(.secondary)
                    }
                    Spacer()
                    StatusBadge(
                        text: model.status?.plex.connected == true ? "Plex Connected" : "Offline",
                        good: model.status?.plex.connected == true
                    )
                    Button("Refresh") { Task { await model.refreshDashboard() } }
                }

                if let s = model.status {
                    infoBox("Plex Server", "\(s.plex.serverName ?? "Unknown") \(s.plex.serverVersion ?? "")")
                    infoBox("Stations", "\(s.enabledStationCount) enabled / \(s.stationCount) configured")
                    infoBox("Versions", "Curator \(s.curatorVersion) • API \(s.apiVersion)")
                    infoBox("Health", model.doctor?.result ?? "Unknown")

                    GroupBox("Libraries") {
                        VStack(alignment: .leading, spacing: 7) {
                            ForEach(s.plex.libraries) { lib in
                                HStack {
                                    Image(systemName: lib.type == "movie" ? "film" : "tv")
                                    Text(lib.name)
                                    Spacer()
                                    Text(lib.type).foregroundColor(.secondary)
                                }
                            }
                        }.frame(maxWidth: .infinity, alignment: .leading)
                    }
                } else {
                    GroupBox("API unavailable") {
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Start the local backend API:")
                            Text("./plex-curator-api serve").font(.system(.body, design: .monospaced))
                            Text("or install the api-server LaunchAgent.").foregroundColor(.secondary)
                        }.frame(maxWidth: .infinity, alignment: .leading)
                    }
                }
            }.padding(24)
        }.navigationTitle("Dashboard")
    }

    private func infoBox(_ title: String, _ value: String) -> some View {
        GroupBox(title) {
            Text(value).font(.title3.bold()).frame(maxWidth: .infinity, alignment: .leading)
        }
    }
}

struct StationsView: View {
    @EnvironmentObject var model: AppModel
    @State private var searchText = ""
    @State private var statusFilter = 0
    @State private var showCreateStation = false

    private var filteredStations: [Station] {
        model.stations.filter { station in
            let matchesStatus: Bool
            switch statusFilter {
            case 1: matchesStatus = station.enabled
            case 2: matchesStatus = !station.enabled
            default: matchesStatus = true
            }

            let query = searchText.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
            guard !query.isEmpty else { return matchesStatus }

            let haystack = [
                station.name,
                station.description ?? "",
                station.playlist,
                station.preset,
                station.includeShows.joined(separator: " "),
                station.excludeShows.joined(separator: " ")
            ].joined(separator: " ").lowercased()

            return matchesStatus && haystack.contains(query)
        }
    }

    var body: some View {
        List(filteredStations) { station in
            NavigationLink(destination: StationDetailView(station: station)) {
                HStack {
                    Image(systemName: station.enabled ? "play.tv.fill" : "pause.tv")
                    VStack(alignment: .leading) {
                        Text(station.name).font(.headline)
                        Text(station.description ?? station.playlist)
                            .font(.caption).foregroundColor(.secondary).lineLimit(1)
                    }
                    Spacer()
                    Text("\(station.total) items").foregroundColor(.secondary)
                }.padding(.vertical, 3)
            }
        }
        .navigationTitle("Stations")
        .searchable(text: $searchText, prompt: "Search stations or shows")
        .toolbar {
            Picker("Status", selection: $statusFilter) {
                Text("All").tag(0)
                Text("Enabled").tag(1)
                Text("Disabled").tag(2)
            }
            .pickerStyle(SegmentedPickerStyle())
            .frame(width: 220)

            Button {
                showCreateStation = true
            } label: {
                Label("New Station", systemImage: "plus")
            }
        }
        .sheet(isPresented: $showCreateStation) {
            StationCreateView()
                .environmentObject(model)
                .frame(minWidth: 480, minHeight: 430)
        }
    }
}

struct StationDetailView: View {
    @EnvironmentObject var model: AppModel
    @Environment(\.dismiss) private var dismiss
    @State private var station: Station
    @State private var tab = 0
    @State private var confirmRefresh = false
    @State private var showEditor = false
    @State private var showClone = false
    @State private var confirmDelete = false

    init(station: Station) {
        _station = State(initialValue: station)
    }

    var body: some View {
        VStack(spacing: 0) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        Text(station.name).font(.title.bold())
                        StatusBadge(text: station.enabled ? "Enabled" : "Disabled", good: station.enabled)
                    }
                    Text(station.playlist).foregroundColor(.secondary)
                }
                Spacer()
                Button("Edit") { showEditor = true }
                Button("Duplicate") { showClone = true }
                Button("Preview") { tab = 1; Task { await model.loadPreview(station) } }
                Button("Diff") { tab = 2; Task { await model.loadDiff(station) } }
                Button("Dry Run") { Task { await model.dryRun(station) } }
                Button("Refresh") { confirmRefresh = true }.disabled(!station.enabled)
                Button("Delete", role: .destructive) { confirmDelete = true }
            }.padding()

            Picker("", selection: $tab) {
                Text("Overview").tag(0); Text("Preview").tag(1); Text("Diff").tag(2)
            }.pickerStyle(SegmentedPickerStyle()).padding(.horizontal)

            Divider().padding(.top, 10)

            if tab == 0 { overview }
            else if tab == 1 { previewList }
            else { diffView }
        }
        .navigationTitle(station.name)
        .sheet(isPresented: $showEditor) {
            StationEditorView(station: station) { updated in
                station = updated
                model.preview = nil
                model.diff = nil
            }
            .environmentObject(model)
            .frame(minWidth: 620, minHeight: 690)
        }
        .sheet(isPresented: $showClone) {
            StationCloneView(station: station)
                .environmentObject(model)
                .frame(minWidth: 480, minHeight: 360)
        }
        .alert("Delete \(station.name)?", isPresented: $confirmDelete) {
            Button("Delete Station", role: .destructive) {
                Task {
                    if await model.deleteStation(station) {
                        dismiss()
                    }
                }
            }
            Button("Cancel", role: .cancel) { }
        } message: {
            Text("This deletes only the station profile. A safety backup is created first. The Plex playlist and station history are left untouched.")
        }
        .alert(isPresented: $confirmRefresh) {
            Alert(
                title: Text("Refresh \(station.name)?"),
                message: Text("This replaces the station's current Plex playlist."),
                primaryButton: .destructive(Text("Refresh")) { Task { await model.refresh(station) } },
                secondaryButton: .cancel()
            )
        }
    }

    private var overview: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 10) {
                row("Enabled", station.enabled ? "Yes" : "No")
                row("Preset", station.preset)
                row("Total", "\(station.total)")
                if station.runtimeBlockMinutes > 0 {
                    row(
                        "Broadcast blocks",
                        "\(station.runtimeBlockCount) × \(station.runtimeBlockMinutes) min"
                    )
                }
                row("Per show", "\(station.perShow)")
                row("Show gap", "\(station.minShowGap)")
                row("Avoid recent", "\(station.avoidRecent)")
                row("Seasonal", station.seasonal)
                row("Watch progress", station.syncWatchProgress ? "Follow Plex" : "Independent")
                row("Years", "\(station.yearMin.map(String.init) ?? "…")–\(station.yearMax.map(String.init) ?? "…")")
                row("Included shows", station.includeShows.isEmpty ? "All qualifying" : station.includeShows.joined(separator: ", "))
                row("Excluded shows", station.excludeShows.isEmpty ? "None" : station.excludeShows.joined(separator: ", "))
            }.padding(22)
        }
    }

    private func row(_ name: String, _ value: String) -> some View {
        HStack(alignment: .top) {
            Text(name).foregroundColor(.secondary).frame(width: 130, alignment: .leading)
            Text(value)
            Spacer()
        }
    }

    private var previewList: some View {
        Group {
            if let p = model.preview, p.station.id == station.id {
                List {
                    if let blocks = p.runtimeBlocks, !blocks.isEmpty {
                        Section("Runtime Blocks") {
                            ForEach(blocks) { block in
                                HStack {
                                    VStack(alignment: .leading, spacing: 2) {
                                        Text("Block \(block.index)")
                                            .font(.headline)
                                        Text(
                                            "Items \(block.startPosition)–\(block.endPosition) • "
                                            + "\(block.itemCount) items"
                                        )
                                        .font(.caption)
                                        .foregroundColor(.secondary)
                                    }
                                    Spacer()
                                    VStack(alignment: .trailing, spacing: 2) {
                                        Text(String(format: "%.1f min", block.durationMinutes))
                                        Text(
                                            String(
                                                format: "%+.1f min vs %d",
                                                block.deltaMinutes,
                                                block.targetMinutes
                                            )
                                        )
                                        .font(.caption)
                                        .foregroundColor(block.complete ? .secondary : .orange)
                                    }
                                }
                            }
                        }
                    }

                    Section("Lineup") {
                        ForEach(p.items) { item in
                            Text(item.displayTitle)
                        }
                    }
                }
            } else {
                Button("Load Preview") { Task { await model.loadPreview(station) } }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
        }
    }

    private var diffView: some View {
        Group {
            if let d = model.diff, d.station.id == station.id {
                VStack {
                    HStack(spacing: 25) {
                        metric("KEEP", d.diff.keepCount)
                        metric("ADD", d.diff.addCount)
                        metric("REMOVE", d.diff.removeCount)
                        metric("MOVED", d.diff.movedCount)
                        Spacer()
                    }.padding()

                    HSplitView {
                        List(d.diff.added, id: \.self) { Label($0, systemImage: "plus.circle") }
                        List(d.diff.removed, id: \.self) { Label($0, systemImage: "minus.circle") }
                    }
                }
            } else {
                Button("Load Diff") { Task { await model.loadDiff(station) } }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
        }
    }

    private func metric(_ name: String, _ value: Int) -> some View {
        VStack { Text("\(value)").font(.title2.bold()); Text(name).font(.caption).foregroundColor(.secondary) }
    }
}

struct StationCreateView: View {
    @EnvironmentObject var model: AppModel
    @Environment(\.dismiss) private var dismiss

    @State private var stationId = ""
    @State private var name = ""
    @State private var description = ""
    @State private var playlist = ""
    @State private var preset = "all-cartoons"
    @State private var enabled = true
    @State private var adult = false
    @State private var validationMessage: String?

    private var normalizedId: String {
        stationId.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
    }

    private var validId: Bool {
        !normalizedId.isEmpty && normalizedId.allSatisfy {
            $0.isLetter || $0.isNumber || $0 == "-" || $0 == "_"
        }
    }

    var body: some View {
        VStack(spacing: 0) {
            HStack {
                Text("New Station").font(.title2.bold())
                Spacer()
                Button("Cancel") { dismiss() }
                Button("Create") { create() }
                    .keyboardShortcut(.defaultAction)
            }
            .padding()

            Divider()

            Form {
                Section("Identity") {
                    TextField("Station ID", text: $stationId)
                    Text("Lowercase letters, numbers, hyphens, and underscores. This ID is permanent.")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    TextField("Name (optional)", text: $name)
                    TextField("Description", text: $description)
                    TextField("Plex playlist (optional)", text: $playlist)
                }

                Section("Programming") {
                    Picker("Preset", selection: $preset) {
                        Text("All Cartoons").tag("all-cartoons")
                        Text("80s Cartoons").tag("80s-cartoons")
                        Text("90s Cartoons").tag("90s-cartoons")
                        Text("Saturday Morning").tag("saturday-morning")
                    }
                    Toggle("Enabled", isOn: $enabled)
                    Toggle("Allow adult animation", isOn: $adult)
                    Text("After creation, open Edit Station for the full programming, interstitial, runtime-block, and show-filter controls.")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }

                if let validationMessage {
                    Section {
                        Text(validationMessage).foregroundColor(.red)
                    }
                }
            }
            .padding()
        }
    }

    private func create() {
        guard validId else {
            validationMessage = "Enter a valid station ID using lowercase letters, numbers, hyphens, or underscores."
            return
        }

        let trimmedName = name.trimmingCharacters(in: .whitespacesAndNewlines)
        let trimmedPlaylist = playlist.trimmingCharacters(in: .whitespacesAndNewlines)
        let request = StationCreateRequest(
            stationId: normalizedId,
            name: trimmedName.isEmpty ? nil : trimmedName,
            description: description.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
                ? nil
                : description.trimmingCharacters(in: .whitespacesAndNewlines),
            playlist: trimmedPlaylist.isEmpty ? nil : trimmedPlaylist,
            preset: preset,
            enabled: enabled,
            adult: adult
        )

        Task {
            if await model.createStation(request) != nil {
                dismiss()
            }
        }
    }
}

struct StationCloneView: View {
    @EnvironmentObject var model: AppModel
    @Environment(\.dismiss) private var dismiss

    let station: Station

    @State private var newStationId: String
    @State private var name: String
    @State private var playlist: String
    @State private var enabled = false
    @State private var validationMessage: String?

    init(station: Station) {
        self.station = station
        _newStationId = State(initialValue: station.id + "-copy")
        _name = State(initialValue: station.name + " Copy")
        _playlist = State(initialValue: station.playlist + " Copy")
    }

    private var normalizedId: String {
        newStationId.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
    }

    private var validId: Bool {
        !normalizedId.isEmpty && normalizedId.allSatisfy {
            $0.isLetter || $0.isNumber || $0 == "-" || $0 == "_"
        }
    }

    var body: some View {
        VStack(spacing: 0) {
            HStack {
                Text("Duplicate Station").font(.title2.bold())
                Spacer()
                Button("Cancel") { dismiss() }
                Button("Duplicate") { duplicate() }
                    .keyboardShortcut(.defaultAction)
            }
            .padding()

            Divider()

            Form {
                Section("Copy of \(station.name)") {
                    TextField("New station ID", text: $newStationId)
                    TextField("Name", text: $name)
                    TextField("Plex playlist", text: $playlist)
                    Toggle("Enable immediately", isOn: $enabled)
                    Text("The duplicate copies all programming rules, filters, interstitial settings, and runtime-block settings. It starts disabled unless you enable it here.")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }

                if let validationMessage {
                    Section {
                        Text(validationMessage).foregroundColor(.red)
                    }
                }
            }
            .padding()
        }
    }

    private func duplicate() {
        guard validId else {
            validationMessage = "Enter a valid station ID using lowercase letters, numbers, hyphens, or underscores."
            return
        }

        let trimmedName = name.trimmingCharacters(in: .whitespacesAndNewlines)
        let trimmedPlaylist = playlist.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmedName.isEmpty, !trimmedPlaylist.isEmpty else {
            validationMessage = "Name and Plex playlist are required."
            return
        }

        let request = StationCloneRequest(
            newStationId: normalizedId,
            name: trimmedName,
            playlist: trimmedPlaylist,
            enabled: enabled
        )

        Task {
            if await model.cloneStation(station, request: request) != nil {
                dismiss()
            }
        }
    }
}

struct StationEditorView: View {
    @EnvironmentObject var model: AppModel
    @Environment(\.dismiss) private var dismiss

    let original: Station
    let onSaved: (Station) -> Void

    @State private var name: String
    @State private var description: String
    @State private var enabled: Bool
    @State private var playlist: String
    @State private var preset: String
    @State private var yearMin: String
    @State private var yearMax: String
    @State private var kidsOnly: Bool
    @State private var adult: Bool
    @State private var perShow: Int
    @State private var total: Int
    @State private var avoidRecent: Int
    @State private var minShowGap: Int
    @State private var seasonal: String
    @State private var specialEvery: Int
    @State private var interstitialPlaylists: Set<String>
    @State private var interstitialTypes: [String: String]
    @State private var interstitialWeights: [String: Int]
    @State private var breakStyle: String
    @State private var interstitialSequence: [String]
    @State private var interstitialBreakPattern: [InterstitialBreakRule]
    @State private var interstitialEvery: Int
    @State private var interstitialCount: Int
    @State private var runtimeBlockMinutes: Int
    @State private var runtimeBlockCount: Int
    @State private var unwatched: Bool
    @State private var syncWatchProgress: Bool
    @State private var includeShows: String
    @State private var excludeShows: String
    @State private var validationMessage: String?

    init(station: Station, onSaved: @escaping (Station) -> Void) {
        original = station
        self.onSaved = onSaved
        _name = State(initialValue: station.name)
        _description = State(initialValue: station.description ?? "")
        _enabled = State(initialValue: station.enabled)
        _playlist = State(initialValue: station.playlist)
        _preset = State(initialValue: station.preset)
        _yearMin = State(initialValue: station.yearMin.map(String.init) ?? "")
        _yearMax = State(initialValue: station.yearMax.map(String.init) ?? "")
        _kidsOnly = State(initialValue: station.kidsOnly)
        _adult = State(initialValue: station.adult)
        _perShow = State(initialValue: station.perShow)
        _total = State(initialValue: station.total)
        _avoidRecent = State(initialValue: station.avoidRecent)
        _minShowGap = State(initialValue: station.minShowGap)
        _seasonal = State(initialValue: station.seasonal)
        _specialEvery = State(initialValue: station.specialEvery)
        let savedPools = station.interstitialPools.isEmpty
            ? station.interstitialPlaylists.map {
                InterstitialPool(playlist: $0, type: "general", weight: 1)
            }
            : station.interstitialPools
        _interstitialPlaylists = State(initialValue: Set(savedPools.map(\.playlist)))
        _interstitialTypes = State(
            initialValue: Dictionary(
                uniqueKeysWithValues: savedPools.map { ($0.playlist, $0.type) }
            )
        )
        _interstitialWeights = State(
            initialValue: Dictionary(
                uniqueKeysWithValues: savedPools.map { ($0.playlist, $0.weight) }
            )
        )
        let savedSequence = station.interstitialSequence ?? []
        let savedPattern = station.interstitialBreakPattern ?? []
        _breakStyle = State(
            initialValue: !savedPattern.isEmpty
                ? "cycle"
                : (!savedSequence.isEmpty ? "ordered" : "weighted")
        )
        _interstitialSequence = State(initialValue: savedSequence)
        _interstitialBreakPattern = State(initialValue: savedPattern)
        _interstitialEvery = State(initialValue: station.interstitialEvery)
        _interstitialCount = State(initialValue: station.interstitialCount)
        _runtimeBlockMinutes = State(initialValue: station.runtimeBlockMinutes)
        _runtimeBlockCount = State(initialValue: station.runtimeBlockCount)
        _unwatched = State(initialValue: station.unwatched)
        _syncWatchProgress = State(initialValue: station.syncWatchProgress)
        _includeShows = State(initialValue: station.includeShows.joined(separator: "\n"))
        _excludeShows = State(initialValue: station.excludeShows.joined(separator: "\n"))
    }

    private var videoPlaylists: [PlaylistSummary] {
        model.playlists
            .filter { ($0.playlistType ?? "video").lowercased() != "audio" }
            .sorted { $0.title.localizedCaseInsensitiveCompare($1.title) == .orderedAscending }
    }

    private var configuredButMissingPlaylists: [String] {
        let available = Set(videoPlaylists.map(\.title))
        return interstitialPlaylists
            .filter { !available.contains($0) }
            .sorted()
    }

    private let interstitialTypeOptions: [(String, String)] = [
        ("general", "General"),
        ("station-id", "Station ID"),
        ("bumper", "Bumper"),
        ("commercial", "Commercial"),
        ("promo", "Promo")
    ]

    private var totalInterstitialWeight: Int {
        interstitialPlaylists.reduce(0) {
            $0 + max(1, interstitialWeights[$1] ?? 1)
        }
    }

    private func interstitialTypeBinding(_ title: String) -> Binding<String> {
        Binding(
            get: { interstitialTypes[title] ?? "general" },
            set: { interstitialTypes[title] = $0 }
        )
    }

    private func interstitialWeightBinding(_ title: String) -> Binding<Int> {
        Binding(
            get: { max(1, interstitialWeights[title] ?? 1) },
            set: { interstitialWeights[title] = max(1, $0) }
        )
    }

    private func selectInterstitial(_ title: String, selected: Bool) {
        if selected {
            interstitialPlaylists.insert(title)
            if interstitialTypes[title] == nil {
                interstitialTypes[title] = "general"
            }
            if interstitialWeights[title] == nil {
                interstitialWeights[title] = 1
            }
        } else {
            interstitialPlaylists.remove(title)
        }
    }

    private func mixPercent(_ title: String) -> Int {
        guard totalInterstitialWeight > 0 else { return 0 }
        let weight = max(1, interstitialWeights[title] ?? 1)
        return Int((Double(weight) / Double(totalInterstitialWeight) * 100.0).rounded())
    }

    private func interstitialWeightLabel(_ title: String) -> String {
        let weight = max(1, interstitialWeights[title] ?? 1)
        if breakStyle != "weighted" {
            return "Weight: \(weight) (within type)"
        }
        return "Weight: \(weight) (~\(mixPercent(title))%)"
    }

    private var orderedBreaksEnabled: Bool { breakStyle == "ordered" }
    private var cyclicBreaksEnabled: Bool { breakStyle == "cycle" }

    private var breakStyleBinding: Binding<String> {
        Binding(
            get: { breakStyle },
            set: { newStyle in
                breakStyle = newStyle
                if newStyle == "ordered" && interstitialSequence.isEmpty {
                    interstitialSequence = ["station-id", "commercial", "bumper"]
                }
                if newStyle == "cycle" && interstitialBreakPattern.isEmpty {
                    interstitialBreakPattern = [
                        InterstitialBreakRule(
                            after: 1,
                            sequence: ["station-id", "bumper"]
                        ),
                        InterstitialBreakRule(
                            after: 2,
                            sequence: ["station-id", "commercial", "commercial", "bumper"]
                        ),
                    ]
                }
            }
        )
    }

    private func interstitialSequenceBinding(_ index: Int) -> Binding<String> {
        Binding(
            get: { interstitialSequence[index] },
            set: { interstitialSequence[index] = $0 }
        )
    }

    private func moveInterstitialStep(_ index: Int, by offset: Int) {
        let target = index + offset
        guard interstitialSequence.indices.contains(index),
              interstitialSequence.indices.contains(target) else { return }
        interstitialSequence.swapAt(index, target)
    }

    private func interstitialBreakAfterBinding(_ index: Int) -> Binding<Int> {
        Binding(
            get: { interstitialBreakPattern[index].after },
            set: { newValue in
                let rule = interstitialBreakPattern[index]
                interstitialBreakPattern[index] = InterstitialBreakRule(
                    after: max(1, newValue),
                    sequence: rule.sequence
                )
            }
        )
    }

    private func interstitialBreakStepBinding(_ breakIndex: Int, _ stepIndex: Int) -> Binding<String> {
        Binding(
            get: { interstitialBreakPattern[breakIndex].sequence[stepIndex] },
            set: { newValue in
                let rule = interstitialBreakPattern[breakIndex]
                var sequence = rule.sequence
                sequence[stepIndex] = newValue
                interstitialBreakPattern[breakIndex] = InterstitialBreakRule(
                    after: rule.after,
                    sequence: sequence
                )
            }
        )
    }

    private func addInterstitialBreakStep(_ breakIndex: Int) {
        let rule = interstitialBreakPattern[breakIndex]
        interstitialBreakPattern[breakIndex] = InterstitialBreakRule(
            after: rule.after,
            sequence: rule.sequence + ["commercial"]
        )
    }

    private func removeInterstitialBreakStep(_ breakIndex: Int, _ stepIndex: Int) {
        let rule = interstitialBreakPattern[breakIndex]
        guard rule.sequence.count > 1 else { return }
        var sequence = rule.sequence
        sequence.remove(at: stepIndex)
        interstitialBreakPattern[breakIndex] = InterstitialBreakRule(
            after: rule.after,
            sequence: sequence
        )
    }

    private func classicAlternatingBreakPattern() {
        interstitialBreakPattern = [
            InterstitialBreakRule(
                after: 1,
                sequence: ["station-id", "bumper"]
            ),
            InterstitialBreakRule(
                after: 2,
                sequence: ["station-id", "commercial", "commercial", "bumper"]
            ),
        ]
    }

    var body: some View {
        VStack(spacing: 0) {
            HStack {
                Text("Edit Station").font(.title2.bold())
                Spacer()
                Button("Cancel") { dismiss() }
                Button("Save") { save() }
                    .keyboardShortcut(.defaultAction)
            }.padding()

            Divider()

            Form {
                Section("Identity") {
                    TextField("Name", text: $name)
                    TextField("Description", text: $description)
                    TextField("Plex playlist", text: $playlist)
                    Toggle("Enabled", isOn: $enabled)
                }

                Section("Programming") {
                    Picker("Preset", selection: $preset) {
                        Text("All Cartoons").tag("all-cartoons")
                        Text("80s Cartoons").tag("80s-cartoons")
                        Text("90s Cartoons").tag("90s-cartoons")
                        Text("Saturday Morning").tag("saturday-morning")
                    }
                    Picker("Seasonal", selection: $seasonal) {
                        Text("Automatic").tag("auto")
                        Text("None").tag("none")
                        Text("Halloween").tag("halloween")
                        Text("Christmas").tag("christmas")
                    }

                    HStack {
                        TextField("Year minimum", text: $yearMin)
                        TextField("Year maximum", text: $yearMax)
                    }

                    Stepper("Episodes per show: \(perShow)", value: $perShow, in: 1...100)
                    Stepper(
                        runtimeBlockMinutes > 0
                            ? "Candidate item floor: \(total)"
                            : "Station length: \(total)",
                        value: $total,
                        in: 1...1000
                    )

                    Toggle(
                        "Runtime-aware broadcast blocks",
                        isOn: Binding(
                            get: { runtimeBlockMinutes > 0 },
                            set: { enabled in
                                runtimeBlockMinutes = enabled
                                    ? max(30, runtimeBlockMinutes)
                                    : 0
                            }
                        )
                    )

                    if runtimeBlockMinutes > 0 {
                        HStack {
                            Button("30 min") { runtimeBlockMinutes = 30 }
                            Button("60 min") { runtimeBlockMinutes = 60 }
                            Button("90 min") { runtimeBlockMinutes = 90 }
                        }

                        Stepper(
                            "Target block: \(runtimeBlockMinutes) minutes",
                            value: $runtimeBlockMinutes,
                            in: 5...180,
                            step: 5
                        )
                        Stepper(
                            "Blocks to build: \(runtimeBlockCount)",
                            value: $runtimeBlockCount,
                            in: 1...96
                        )

                        Text("Curator counts both programs and interstitials, then ends each block at the nearest complete item boundary. The candidate item floor only ensures enough material is available.")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }

                    Stepper("Avoid recent: \(avoidRecent)", value: $avoidRecent, in: 0...100000)
                    Stepper("Minimum show gap: \(minShowGap)", value: $minShowGap, in: 0...100)
                    Stepper("Special every: \(specialEvery)", value: $specialEvery, in: 1...1000)
                }

                Section("Interstitials") {
                    Text("Choose Plex video playlists, then assign each pool a type and relative weight.")
                        .font(.caption)
                        .foregroundColor(.secondary)

                    if model.playlists.isEmpty {
                        HStack {
                            ProgressView()
                            Text("Loading Plex playlists…")
                                .foregroundColor(.secondary)
                        }
                    } else if videoPlaylists.isEmpty && configuredButMissingPlaylists.isEmpty {
                        Text("No Plex video playlists found.")
                            .foregroundColor(.secondary)
                    } else {
                        ForEach(videoPlaylists) { plexPlaylist in
                            VStack(alignment: .leading, spacing: 8) {
                                Toggle(
                                    "\(plexPlaylist.title)\(plexPlaylist.itemCount.map { " (\($0))" } ?? "")",
                                    isOn: Binding(
                                        get: { interstitialPlaylists.contains(plexPlaylist.title) },
                                        set: { selectInterstitial(plexPlaylist.title, selected: $0) }
                                    )
                                )

                                if interstitialPlaylists.contains(plexPlaylist.title) {
                                    HStack {
                                        Picker("Type", selection: interstitialTypeBinding(plexPlaylist.title)) {
                                            ForEach(interstitialTypeOptions, id: \.0) { option in
                                                Text(option.1).tag(option.0)
                                            }
                                        }
                                        .frame(maxWidth: 220)

                                        Stepper(
                                            interstitialWeightLabel(plexPlaylist.title),
                                            value: interstitialWeightBinding(plexPlaylist.title),
                                            in: 1...1000
                                        )
                                    }
                                    .padding(.leading, 18)
                                }
                            }
                        }

                        ForEach(configuredButMissingPlaylists, id: \.self) { title in
                            VStack(alignment: .leading, spacing: 8) {
                                Toggle(
                                    "\(title) (not currently found in Plex)",
                                    isOn: Binding(
                                        get: { interstitialPlaylists.contains(title) },
                                        set: { selectInterstitial(title, selected: $0) }
                                    )
                                )
                                .foregroundColor(.secondary)

                                if interstitialPlaylists.contains(title) {
                                    HStack {
                                        Picker("Type", selection: interstitialTypeBinding(title)) {
                                            ForEach(interstitialTypeOptions, id: \.0) { option in
                                                Text(option.1).tag(option.0)
                                            }
                                        }
                                        .frame(maxWidth: 220)

                                        Stepper(
                                            interstitialWeightLabel(title),
                                            value: interstitialWeightBinding(title),
                                            in: 1...1000
                                        )
                                    }
                                    .padding(.leading, 18)
                                }
                            }
                        }
                    }

                    Picker("Break style", selection: breakStyleBinding) {
                        Text("Weighted mix").tag("weighted")
                        Text("Ordered sequence").tag("ordered")
                        Text("Cyclic pattern").tag("cycle")
                    }

                    if cyclicBreaksEnabled {
                        Text("Each rule controls both when the next break happens and which clip types play. The rules repeat as a cycle.")
                            .font(.caption)
                            .foregroundColor(.secondary)

                        ForEach(Array(interstitialBreakPattern.indices), id: \.self) { breakIndex in
                            GroupBox("Break \(breakIndex + 1)") {
                                VStack(alignment: .leading, spacing: 8) {
                                    Stepper(
                                        "After \(interstitialBreakPattern[breakIndex].after) program item\(interstitialBreakPattern[breakIndex].after == 1 ? "" : "s")",
                                        value: interstitialBreakAfterBinding(breakIndex),
                                        in: 1...1000
                                    )

                                    ForEach(Array(interstitialBreakPattern[breakIndex].sequence.indices), id: \.self) { stepIndex in
                                        HStack {
                                            Text("\(stepIndex + 1).")
                                                .font(.caption.monospacedDigit())
                                                .foregroundColor(.secondary)
                                                .frame(width: 24, alignment: .trailing)

                                            Picker(
                                                "Clip \(stepIndex + 1)",
                                                selection: interstitialBreakStepBinding(breakIndex, stepIndex)
                                            ) {
                                                ForEach(interstitialTypeOptions, id: \.0) { option in
                                                    Text(option.1).tag(option.0)
                                                }
                                            }
                                            .labelsHidden()

                                            Button(role: .destructive) {
                                                removeInterstitialBreakStep(breakIndex, stepIndex)
                                            } label: {
                                                Image(systemName: "trash")
                                            }
                                            .disabled(interstitialBreakPattern[breakIndex].sequence.count <= 1)
                                        }
                                    }

                                    HStack {
                                        Button("Add Clip") {
                                            addInterstitialBreakStep(breakIndex)
                                        }
                                        Spacer()
                                        Button("Remove Break", role: .destructive) {
                                            interstitialBreakPattern.remove(at: breakIndex)
                                        }
                                    }
                                }
                                .padding(4)
                            }
                        }

                        HStack {
                            Button("Add Break") {
                                interstitialBreakPattern.append(
                                    InterstitialBreakRule(
                                        after: 1,
                                        sequence: ["commercial"]
                                    )
                                )
                            }
                            Button("Classic Alternating") {
                                classicAlternatingBreakPattern()
                            }
                        }
                    } else {
                        Stepper(
                            interstitialEvery == 0
                                ? "Break frequency: Off"
                                : "Break every \(interstitialEvery) program items",
                            value: $interstitialEvery,
                            in: 0...1000
                        )
                    }

                    if orderedBreaksEnabled {
                        Text("Each break follows these steps in order. Repeat a type to play more than one clip of that kind.")
                            .font(.caption)
                            .foregroundColor(.secondary)

                        ForEach(Array(interstitialSequence.indices), id: \.self) { index in
                            HStack {
                                Text("\(index + 1).")
                                    .font(.caption.monospacedDigit())
                                    .foregroundColor(.secondary)
                                    .frame(width: 24, alignment: .trailing)

                                Picker("Step \(index + 1)", selection: interstitialSequenceBinding(index)) {
                                    ForEach(interstitialTypeOptions, id: \.0) { option in
                                        Text(option.1).tag(option.0)
                                    }
                                }
                                .labelsHidden()

                                Button {
                                    moveInterstitialStep(index, by: -1)
                                } label: {
                                    Image(systemName: "arrow.up")
                                }
                                .disabled(index == interstitialSequence.startIndex)

                                Button {
                                    moveInterstitialStep(index, by: 1)
                                } label: {
                                    Image(systemName: "arrow.down")
                                }
                                .disabled(index == interstitialSequence.index(before: interstitialSequence.endIndex))

                                Button(role: .destructive) {
                                    interstitialSequence.remove(at: index)
                                } label: {
                                    Image(systemName: "trash")
                                }
                            }
                        }

                        HStack {
                            Button("Add Step") {
                                interstitialSequence.append("commercial")
                            }
                            Button("Classic TV Break") {
                                interstitialSequence = ["station-id", "commercial", "commercial", "bumper"]
                            }
                        }
                    } else if !cyclicBreaksEnabled {
                        Stepper(
                            "Clips per break: \(interstitialCount)",
                            value: $interstitialCount,
                            in: 1...20
                        )
                        .disabled(interstitialEvery == 0)
                    }

                    if interstitialPlaylists.isEmpty {
                        Text("Select at least one playlist to use interstitials.")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    } else if !cyclicBreaksEnabled && interstitialEvery == 0 {
                        Text("Pools are configured, but insertion is disabled until break frequency is above 0.")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    } else if cyclicBreaksEnabled {
                        Text("Cyclic mode ignores the single break-frequency setting. Pool weights only choose between playlists of the same requested type.")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    } else if orderedBreaksEnabled {
                        Text("Ordered mode uses pool weights only when more than one playlist can satisfy the same step type.")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    } else {
                        Text("Weights are relative. For example 20 / 35 / 45 behaves like 20% / 35% / 45%.")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }

                Section("Audience / Progress") {
                    Toggle("Kids-only filtering", isOn: $kidsOnly)
                    Toggle("Allow adult animation", isOn: $adult)
                    Toggle("Prefer unwatched episodes", isOn: $unwatched)
                    Toggle("Follow Plex watch progress", isOn: $syncWatchProgress)
                }

                Section("Show Overrides") {
                    Text("One show title per line.")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    TextEditor(text: $includeShows).frame(minHeight: 80)
                    Text("Included shows")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    TextEditor(text: $excludeShows).frame(minHeight: 80)
                    Text("Excluded shows")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }

                if let validationMessage {
                    Section {
                        Text(validationMessage).foregroundColor(.red)
                    }
                }
            }
            .padding()
        }
        .task {
            if model.playlists.isEmpty {
                await model.loadPlaylists()
            }
        }
    }

    private func parsedYear(_ value: String) -> Int? {
        let trimmed = value.trimmingCharacters(in: .whitespacesAndNewlines)
        return trimmed.isEmpty ? nil : Int(trimmed)
    }

    private func lines(_ value: String) -> [String] {
        value.split(separator: "\n")
            .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }
    }

    private func save() {
        guard !name.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            validationMessage = "Name is required."
            return
        }
        guard !playlist.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            validationMessage = "Playlist name is required."
            return
        }

        let minYear = parsedYear(yearMin)
        let maxYear = parsedYear(yearMax)
        if !yearMin.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty && minYear == nil {
            validationMessage = "Minimum year must be a number."
            return
        }
        if !yearMax.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty && maxYear == nil {
            validationMessage = "Maximum year must be a number."
            return
        }
        if let minYear, let maxYear, minYear > maxYear {
            validationMessage = "Minimum year cannot be greater than maximum year."
            return
        }
        if orderedBreaksEnabled && interstitialSequence.isEmpty {
            validationMessage = "Ordered breaks need at least one step."
            return
        }
        if cyclicBreaksEnabled && interstitialBreakPattern.isEmpty {
            validationMessage = "Cyclic breaks need at least one break rule."
            return
        }
        if cyclicBreaksEnabled && interstitialBreakPattern.contains(where: { $0.sequence.isEmpty }) {
            validationMessage = "Every cyclic break rule needs at least one clip type."
            return
        }

        let request = StationUpdateRequest(
            name: name.trimmingCharacters(in: .whitespacesAndNewlines),
            description: description,
            enabled: enabled,
            playlist: playlist.trimmingCharacters(in: .whitespacesAndNewlines),
            preset: preset,
            yearMin: minYear,
            yearMax: maxYear,
            kidsOnly: kidsOnly,
            adult: adult,
            perShow: perShow,
            total: total,
            avoidRecent: avoidRecent,
            minShowGap: minShowGap,
            seasonal: seasonal,
            specialEvery: specialEvery,
            interstitialPlaylists: interstitialPlaylists.sorted(),
            interstitialPools: interstitialPlaylists.sorted().map {
                InterstitialPool(
                    playlist: $0,
                    type: interstitialTypes[$0] ?? "general",
                    weight: max(1, interstitialWeights[$0] ?? 1)
                )
            },
            interstitialSequence: orderedBreaksEnabled ? interstitialSequence : [],
            interstitialBreakPattern: cyclicBreaksEnabled ? interstitialBreakPattern : [],
            interstitialEvery: interstitialEvery,
            interstitialCount: interstitialCount,
            runtimeBlockMinutes: runtimeBlockMinutes,
            runtimeBlockCount: runtimeBlockCount,
            unwatched: unwatched,
            syncWatchProgress: syncWatchProgress,
            includeShows: lines(includeShows),
            excludeShows: lines(excludeShows)
        )

        Task {
            if let updated = await model.updateStation(original, request: request) {
                onSaved(updated)
                dismiss()
            }
        }
    }
}

enum MediaOrganizerFilter: String, CaseIterable, Identifiable {
    case review = "Needs Review"
    case ready = "Ready to Apply"
    case unchanged = "Already Organized"
    case all = "All"

    var id: String { rawValue }
}

struct MediaOrganizerView: View {
    @EnvironmentObject var model: AppModel

    @State private var sourcePath = ""
    @State private var destinationPath = ""
    @State private var recursive = true
    @State private var includeLowConfidence = false
    @State private var confirmApply = false
    @State private var reviewedSources: Set<String> = []
    @State private var reviewedTitles: [String: String] = [:]
    @State private var reviewedTypes: [String: String] = [:]
    @State private var organizerFilter: MediaOrganizerFilter = .review
    @State private var organizerSearch = ""
    @State private var excludePatternsText = ""
    @State private var deleteExcluded = false
    @State private var selectedPresetID = ""
    @State private var presetName = ""
    @State private var presetDescription = ""

    private var plan: MediaOrganizerResponse? { model.mediaOrganizer }

    private var unresolvedReviewCount: Int {
        plan?.items.filter {
            $0.confidence == "low" &&
            $0.reviewed != true &&
            !reviewedSources.contains($0.source)
        }.count ?? 0
    }

    private var filteredItems: [MediaOrganizerItem] {
        guard let plan else { return [] }
        let query = organizerSearch
            .trimmingCharacters(in: .whitespacesAndNewlines)
            .lowercased()

        return plan.items.filter { item in
            let matchesFilter: Bool
            switch organizerFilter {
            case .review:
                matchesFilter =
                    item.confidence == "low" &&
                    item.reviewed != true &&
                    !reviewedSources.contains(item.source)
            case .ready:
                matchesFilter =
                    item.action != "unchanged" &&
                    (
                        includeLowConfidence ||
                        item.confidence != "low" ||
                        item.reviewed == true ||
                        reviewedSources.contains(item.source)
                    )
            case .unchanged:
                matchesFilter = item.action == "unchanged"
            case .all:
                matchesFilter = true
            }

            guard matchesFilter else { return false }
            guard !query.isEmpty else { return true }

            let reviewedTitle = reviewedTitles[item.source] ?? item.title
            let reviewedType = reviewedTypes[item.source] ?? item.type
            return [
                item.originalName,
                item.proposedName,
                item.source,
                item.folder,
                reviewedTitle,
                reviewedType,
                item.metadataTitle ?? ""
            ]
            .joined(separator: " ")
            .lowercased()
            .contains(query)
        }
    }

    private var actionableCount: Int {
        plan?.items.filter {
            $0.action != "unchanged" &&
            (
                includeLowConfidence ||
                $0.confidence != "low" ||
                reviewedSources.contains($0.source)
            )
        }.count ?? 0
    }

    private var reviewedOverrides: [MediaOrganizerOverrideRequest] {
        guard let plan else { return [] }
        return plan.items.compactMap { item in
            let hasReview = reviewedSources.contains(item.source)
            let editedTitle = reviewedTitles[item.source]
            let editedType = reviewedTypes[item.source]
            let changed = (editedTitle != nil && editedTitle != item.title) ||
                (editedType != nil && editedType != item.type)
            guard hasReview || changed else { return nil }
            return MediaOrganizerOverrideRequest(
                source: item.source,
                title: (editedTitle ?? item.title).trimmingCharacters(in: .whitespacesAndNewlines),
                type: editedType ?? item.type
            )
        }
    }

    private func titleBinding(_ item: MediaOrganizerItem) -> Binding<String> {
        Binding(
            get: { reviewedTitles[item.source] ?? item.title },
            set: { value in
                reviewedTitles[item.source] = value
                reviewedSources.insert(item.source)
            }
        )
    }

    private func typeBinding(_ item: MediaOrganizerItem) -> Binding<String> {
        Binding(
            get: { reviewedTypes[item.source] ?? item.type },
            set: { value in
                reviewedTypes[item.source] = value
                reviewedSources.insert(item.source)
            }
        )
    }

    private func reviewedBinding(_ item: MediaOrganizerItem) -> Binding<Bool> {
        Binding(
            get: { reviewedSources.contains(item.source) || item.reviewed == true },
            set: { selected in
                if selected {
                    reviewedSources.insert(item.source)
                    if reviewedTitles[item.source] == nil {
                        reviewedTitles[item.source] = item.title
                    }
                    if reviewedTypes[item.source] == nil {
                        reviewedTypes[item.source] = item.type
                    }
                } else {
                    reviewedSources.remove(item.source)
                }
            }
        )
    }

    private var excludePatterns: [String] {
        excludePatternsText
            .split(whereSeparator: { $0 == "\n" || $0 == "," })
            .map { String($0).trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }
    }

    private var excludedCount: Int {
        plan?.excludedCount ?? 0
    }

    private var selectedPreset: MediaOrganizerPreset? {
        model.mediaOrganizerPresets.first { $0.id == selectedPresetID }
    }

    private var canSavePreset: Bool {
        !presetName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }

    private func loadPreset(_ preset: MediaOrganizerPreset) {
        selectedPresetID = preset.id
        presetName = preset.name
        presetDescription = preset.description
        excludePatternsText = preset.excludePatterns.joined(separator: "\n")
        deleteExcluded = false
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Media Organizer")
                        .font(.largeTitle.bold())
                    Text("Scan interstitial video folders, preview clean names and categories, visually inspect mystery clips, then safely organize the files.")
                        .foregroundColor(.secondary)
                }
                Spacer()
            }

            GroupBox("Folders") {
                VStack(alignment: .leading, spacing: 10) {
                    HStack {
                        TextField("Source folder", text: $sourcePath)
                        Button("Browse…") { chooseFolder { sourcePath = $0 } }
                    }

                    HStack {
                        TextField("Destination folder (optional)", text: $destinationPath)
                        Button("Browse…") { chooseFolder { destinationPath = $0 } }
                        Button("Use Source") { destinationPath = "" }
                    }

                    Toggle("Scan subfolders recursively", isOn: $recursive)

                    VStack(alignment: .leading, spacing: 8) {
                        Text("Exclusion preset")
                            .font(.headline)

                        HStack {
                            Picker("Preset", selection: $selectedPresetID) {
                                Text("Custom / Unsaved").tag("")
                                ForEach(model.mediaOrganizerPresets) { preset in
                                    Text(preset.name).tag(preset.id)
                                }
                            }
                            .frame(maxWidth: 260)
                            .onChange(of: selectedPresetID) { newValue in
                                guard !newValue.isEmpty,
                                      let preset = model.mediaOrganizerPresets.first(where: { $0.id == newValue })
                                else { return }
                                loadPreset(preset)
                            }

                            TextField("Preset name", text: $presetName)
                                .frame(maxWidth: 220)

                            Button(selectedPresetID.isEmpty ? "Save New" : "Update") {
                                Task {
                                    if let saved = await model.saveMediaOrganizerPreset(
                                        id: selectedPresetID.isEmpty ? nil : selectedPresetID,
                                        name: presetName,
                                        description: presetDescription,
                                        excludePatterns: excludePatterns
                                    ) {
                                        loadPreset(saved)
                                    }
                                }
                            }
                            .disabled(!canSavePreset)

                            if !selectedPresetID.isEmpty {
                                Button("Save As New") {
                                    Task {
                                        if let saved = await model.saveMediaOrganizerPreset(
                                            id: nil,
                                            name: presetName,
                                            description: presetDescription,
                                            excludePatterns: excludePatterns,
                                            createNew: true
                                        ) {
                                            loadPreset(saved)
                                        }
                                    }
                                }
                                .disabled(!canSavePreset)

                                Button("Delete Preset", role: .destructive) {
                                    let deleting = selectedPresetID
                                    Task {
                                        if await model.deleteMediaOrganizerPreset(id: deleting) {
                                            selectedPresetID = ""
                                            presetName = ""
                                            presetDescription = ""
                                        }
                                    }
                                }
                            }
                        }

                        TextField("Preset description (optional)", text: $presetDescription)

                        HStack {
                            Text("Exclude patterns")
                                .font(.headline)
                            Spacer()
                            Button("Add Sample Rules") {
                                let preset = ["sample.*", "*/sample/*"]
                                let existing = Set(excludePatterns.map { $0.lowercased() })
                                let additions = preset.filter { !existing.contains($0.lowercased()) }
                                let current = excludePatternsText.trimmingCharacters(in: .whitespacesAndNewlines)
                                excludePatternsText = ([current].filter { !$0.isEmpty } + additions)
                                    .joined(separator: "\n")
                                selectedPresetID = ""
                            }
                        }

                        TextEditor(text: $excludePatternsText)
                            .font(.system(.body, design: .monospaced))
                            .frame(minHeight: 58, maxHeight: 92)
                            .overlay(
                                RoundedRectangle(cornerRadius: 6)
                                    .stroke(.quaternary)
                            )

                        if let selectedPreset {
                            Text("Loaded preset: \(selectedPreset.name). Editing rules does not change the saved preset until Update is clicked.")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }

                        Text("Case-insensitive glob patterns, one per line or comma-separated. Examples: Sample.avi, sample.*, */sample/*")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }

                    HStack {
                        Button {
                            Task { await scan() }
                        } label: {
                            Label("Scan / Preview", systemImage: "magnifyingglass")
                        }
                        .disabled(sourcePath.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || model.mediaOrganizerScanning)

                        if model.mediaOrganizerScanning {
                            ProgressView()
                                .controlSize(.small)
                        }

                        Spacer()

                        Text("Preview-only until Apply is confirmed.")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
                .padding(4)
                .disabled(model.mediaOrganizerScanning)
            }

            if let scanJob = model.mediaOrganizerScanJob {
                GroupBox("Scan Progress") {
                    VStack(alignment: .leading, spacing: 10) {
                        HStack {
                            VStack(alignment: .leading, spacing: 3) {
                                Text(scanProgressTitle(scanJob))
                                    .font(.headline)
                                if let detail = scanJob.detail, !detail.isEmpty, scanJob.isActive {
                                    Text(detail)
                                        .font(.caption)
                                        .foregroundColor(.secondary)
                                        .lineLimit(1)
                                        .truncationMode(.middle)
                                }
                            }

                            Spacer()

                            Text(formatElapsed(scanJob.elapsedSeconds))
                                .font(.caption.monospacedDigit())
                                .foregroundColor(.secondary)

                            if scanJob.isActive {
                                Button("Cancel Scan", role: .destructive) {
                                    Task { await model.cancelMediaOrganizerScan() }
                                }
                                .disabled(scanJob.cancelRequested || scanJob.status == "cancelling")
                            }
                        }

                        if scanJob.phase == "analyzing",
                           let total = scanJob.totalCount,
                           total > 0 {
                            ProgressView(
                                value: Double(scanJob.processedCount),
                                total: Double(total)
                            )
                        } else if scanJob.isActive {
                            ProgressView()
                        } else if scanJob.status == "completed" {
                            ProgressView(value: 1, total: 1)
                        }

                        HStack(spacing: 16) {
                            if scanJob.discoveredCount > 0 {
                                Label(
                                    "\(scanJob.discoveredCount) found",
                                    systemImage: "film.stack"
                                )
                            }
                            if let total = scanJob.totalCount, total > 0 {
                                Label(
                                    "\(scanJob.processedCount) / \(total) analyzed",
                                    systemImage: "magnifyingglass"
                                )
                            }
                            if scanJob.excludedCount > 0 {
                                Label(
                                    "\(scanJob.excludedCount) excluded",
                                    systemImage: "nosign"
                                )
                            }
                        }
                        .font(.caption)
                        .foregroundColor(.secondary)
                    }
                    .padding(4)
                }
            }

            if let plan {
                HStack(spacing: 12) {
                    organizerMetric("Videos", plan.count)
                    organizerMetric("Excluded", excludedCount)
                    organizerMetric("Needs Review", unresolvedReviewCount)
                    organizerMetric("Will Change", actionableCount)
                    Spacer()
                    Text(plan.destination)
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .lineLimit(1)
                        .truncationMode(.middle)
                }

                HStack(spacing: 12) {
                    Picker("Show", selection: $organizerFilter) {
                        ForEach(MediaOrganizerFilter.allCases) { filter in
                            Text(filter.rawValue).tag(filter)
                        }
                    }
                    .pickerStyle(.segmented)
                    .frame(maxWidth: 620)

                    TextField("Search files, titles, folders…", text: $organizerSearch)
                        .textFieldStyle(.roundedBorder)
                }

                if let excluded = plan.excludedItems, !excluded.isEmpty {
                    DisclosureGroup("Excluded Files (\(excluded.count))") {
                        VStack(alignment: .leading, spacing: 6) {
                            ForEach(excluded.prefix(100)) { item in
                                HStack {
                                    Image(systemName: "nosign")
                                        .foregroundColor(.secondary)
                                    Text(item.relativePath)
                                        .lineLimit(1)
                                        .truncationMode(.middle)
                                    Spacer()
                                    Text(item.matchedPattern)
                                        .font(.caption.monospaced())
                                        .foregroundColor(.secondary)
                                }
                            }
                            if excluded.count > 100 {
                                Text("Showing first 100 of \(excluded.count) excluded files.")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                        }
                        .padding(.top, 6)
                    }
                }

                GroupBox("Proposed Changes") {
                    if plan.items.isEmpty {
                        Text("No supported video files were found.")
                            .foregroundColor(.secondary)
                            .frame(maxWidth: .infinity, minHeight: 160)
                    } else if filteredItems.isEmpty {
                        VStack(spacing: 8) {
                            Image(systemName: organizerFilter == .review ? "checkmark.circle" : "line.3.horizontal.decrease.circle")
                                .font(.system(size: 32))
                                .foregroundColor(.secondary)
                            Text(
                                organizerFilter == .review && organizerSearch.isEmpty
                                    ? "Review queue is clear."
                                    : "No files match this filter."
                            )
                            .font(.headline)
                            Text(
                                organizerFilter == .review && organizerSearch.isEmpty
                                    ? "Low-confidence files will appear here after the next scan."
                                    : "Try another filter or search term."
                            )
                            .font(.caption)
                            .foregroundColor(.secondary)
                        }
                        .frame(maxWidth: .infinity, minHeight: 180)
                    } else {
                        List(filteredItems) { item in
                            MediaOrganizerRow(
                                item: item,
                                destination: normalizedDestination,
                                reviewedTitle: titleBinding(item),
                                reviewedType: typeBinding(item),
                                reviewed: reviewedBinding(item),
                                onAnalyzed: { analyzed in
                                    reviewedTitles[item.source] = analyzed.title
                                    reviewedTypes[item.source] = analyzed.type
                                }
                            )
                        }
                        .frame(minHeight: 320)
                    }
                }

                HStack {
                    Toggle("Include low-confidence filename guesses", isOn: $includeLowConfidence)
                        .help("Low-confidence files look like generic names such as video_0047.mp4 and are skipped by default.")

                    if excludedCount > 0 {
                        Toggle("Delete excluded files", isOn: $deleteExcluded)
                            .help("Permanently deletes only files matched by the explicit exclude patterns when Apply is confirmed.")
                    }

                    Spacer()

                    Button(role: .destructive) {
                        confirmApply = true
                    } label: {
                        Label("Apply \(actionableCount) Changes", systemImage: "folder.badge.plus")
                    }
                    .disabled(actionableCount == 0 || model.loading || model.mediaOrganizerScanning)
                }

                if unresolvedReviewCount > 0 && !includeLowConfidence {
                    Label(
                        "\(unresolvedReviewCount) low-confidence file\(unresolvedReviewCount == 1 ? "" : "s") will remain untouched for review.",
                        systemImage: "exclamationmark.triangle"
                    )
                    .font(.caption)
                    .foregroundColor(.secondary)
                }
            } else {
                VStack(spacing: 12) {
                    Image(systemName: "folder")
                        .font(.system(size: 42))
                        .foregroundColor(.secondary)
                    Text("Choose a Media Folder")
                        .font(.title2.bold())
                    Text("Curator will inspect supported videos and propose organized Station IDs, Bumpers, Commercials, Promos, and General folders.")
                        .foregroundColor(.secondary)
                        .multilineTextAlignment(.center)
                        .frame(maxWidth: 520)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
        }
        .padding()
        .navigationTitle("Media Organizer")
        .task {
            if model.mediaOrganizerPresets.isEmpty {
                await model.loadMediaOrganizerPresets()
            }
        }
        .alert("Apply file organization?", isPresented: $confirmApply) {
            Button("Cancel", role: .cancel) {}
            Button("Move & Rename", role: .destructive) {
                Task {
                    let ok = await model.applyMediaOrganizer(
                        path: sourcePath,
                        destination: normalizedDestination,
                        recursive: recursive,
                        includeLowConfidence: includeLowConfidence,
                        deleteExcluded: deleteExcluded,
                        excludePatterns: excludePatterns,
                        overrides: reviewedOverrides
                    )
                    if ok {
                        await scan()
                    }
                }
            }
        } message: {
            Text(
                "Curator will move and rename \(actionableCount) file\(actionableCount == 1 ? "" : "s")." +
                (deleteExcluded && excludedCount > 0 ? " It will also permanently delete \(excludedCount) excluded file\(excludedCount == 1 ? "" : "s")." : "") +
                " Existing files are never overwritten, and a JSON manifest is saved for the operation."
            )
        }
    }

    private func scanProgressTitle(_ job: MediaOrganizerScanJob) -> String {
        switch job.status {
        case "queued":
            return "Scan queued…"
        case "cancelling":
            return "Cancelling scan…"
        case "cancelled":
            return "Scan cancelled"
        case "failed":
            return "Scan failed"
        case "completed":
            return "Scan complete"
        default:
            switch job.phase {
            case "discovering":
                return job.discoveredCount > 0
                    ? "Finding videos… \(job.discoveredCount) found"
                    : "Finding videos…"
            case "analyzing":
                if let total = job.totalCount, total > 0 {
                    return "Analyzing \(job.processedCount) of \(total) files"
                }
                return "Analyzing files…"
            case "finalizing":
                return "Finalizing scan results…"
            default:
                return "Scanning…"
            }
        }
    }

    private func formatElapsed(_ seconds: Double) -> String {
        let total = max(0, Int(seconds.rounded()))
        if total >= 3600 {
            return String(format: "%d:%02d:%02d", total / 3600, (total % 3600) / 60, total % 60)
        }
        return String(format: "%d:%02d", total / 60, total % 60)
    }

    private var normalizedDestination: String? {
        let trimmed = destinationPath.trimmingCharacters(in: .whitespacesAndNewlines)
        return trimmed.isEmpty ? nil : trimmed
    }

    private func scan() async {
        reviewedSources.removeAll()
        reviewedTitles.removeAll()
        reviewedTypes.removeAll()
        organizerFilter = .review
        organizerSearch = ""
        await model.scanMediaOrganizer(
            path: sourcePath.trimmingCharacters(in: .whitespacesAndNewlines),
            destination: normalizedDestination,
            recursive: recursive,
            excludePatterns: excludePatterns
        )
    }

    private func chooseFolder(_ completion: (String) -> Void) {
        let panel = NSOpenPanel()
        panel.title = "Choose Media Folder"
        panel.prompt = "Choose"
        panel.canChooseFiles = false
        panel.canChooseDirectories = true
        panel.allowsMultipleSelection = false
        panel.canCreateDirectories = true
        if panel.runModal() == .OK, let url = panel.url {
            completion(url.path)
        }
    }

    private func organizerMetric(_ label: String, _ value: Int) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            Text("\(value)")
                .font(.title2.bold())
            Text(label)
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 8)
        .background(.quaternary, in: RoundedRectangle(cornerRadius: 8))
    }
}

struct MediaOrganizerRow: View {
    @EnvironmentObject var model: AppModel
    let item: MediaOrganizerItem
    let destination: String?
    @Binding var reviewedTitle: String
    @Binding var reviewedType: String
    @Binding var reviewed: Bool
    let onAnalyzed: (MediaOrganizerItem) -> Void

    @State private var analyzing = false
    @State private var visualSuggestion: MediaVisualSuggestion?

    private var displayItem: MediaOrganizerItem {
        model.analyzedMediaItems[item.source] ?? item
    }

    private var confidenceSymbol: String {
        switch item.confidence {
        case "high": return "checkmark.seal.fill"
        case "medium": return "checkmark.circle"
        default: return "exclamationmark.triangle.fill"
        }
    }

    private var confidenceText: String {
        item.confidence.capitalized
    }

    private var typeText: String {
        switch item.type {
        case "station-id": return "Station ID"
        case "bumper": return "Bumper"
        case "commercial": return "Commercial"
        case "promo": return "Promo"
        default: return "General"
        }
    }

    private var reviewFrameMessage: String {
        switch displayItem.reviewFrameStatus {
        case "ffmpeg-missing":
            return "Visual review unavailable: ffmpeg is not installed."
        case "duration-unavailable":
            return "Visual review unavailable: video duration could not be read."
        case "failed":
            return "Visual review frames could not be extracted."
        case "deferred":
            return "Visual review deferred for fast bulk scanning."
        default:
            return "No visual review frames available."
        }
    }

    private func formatTimestamp(_ seconds: Double) -> String {
        let total = max(0, Int(seconds.rounded()))
        return String(format: "%d:%02d", total / 60, total % 60)
    }

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: confidenceSymbol)
                .frame(width: 22)
                .foregroundColor(item.confidence == "low" ? .orange : .secondary)

            VStack(alignment: .leading, spacing: 5) {
                Text(item.originalName)
                    .font(.headline)
                    .lineLimit(1)

                HStack(spacing: 6) {
                    Text("→")
                        .foregroundColor(.secondary)
                    Text("\(item.folder)/\(item.proposedName)")
                        .lineLimit(1)
                        .truncationMode(.middle)
                }
                .font(.callout)

                HStack(spacing: 12) {
                    Label(typeText, systemImage: "tag")
                    Label(confidenceText, systemImage: "waveform.path.ecg")
                    Text("Name from \(item.titleSource)")
                }
                .font(.caption)
                .foregroundColor(.secondary)

                if let frames = displayItem.reviewFrames, !frames.isEmpty {
                    HStack(spacing: 8) {
                        ForEach(frames) { frame in
                            if let url = model.api.mediaOrganizerFrameURL(frame.frameId) {
                                VStack(alignment: .leading, spacing: 3) {
                                    AsyncImage(url: url) { phase in
                                        switch phase {
                                        case .empty:
                                            ZStack {
                                                RoundedRectangle(cornerRadius: 6)
                                                    .fill(.quaternary)
                                                ProgressView()
                                                    .controlSize(.small)
                                            }
                                        case .success(let image):
                                            image
                                                .resizable()
                                                .scaledToFill()
                                        case .failure:
                                            ZStack {
                                                RoundedRectangle(cornerRadius: 6)
                                                    .fill(.quaternary)
                                                Image(systemName: "photo")
                                                    .foregroundColor(.secondary)
                                            }
                                        @unknown default:
                                            EmptyView()
                                        }
                                    }
                                    .frame(width: 150, height: 84)
                                    .clipShape(RoundedRectangle(cornerRadius: 6))

                                    Text(formatTimestamp(frame.timestampSeconds))
                                        .font(.caption2.monospacedDigit())
                                        .foregroundColor(.secondary)
                                }
                            }
                        }
                    }
                    .padding(.top, 4)
                } else if displayItem.confidence == "low" {
                    Text(reviewFrameMessage)
                        .font(.caption2)
                        .foregroundColor(.secondary)
                }

                if item.confidence == "low" && (displayItem.reviewFrames ?? []).isEmpty {
                    Button {
                        analyzing = true
                        Task {
                            if let analyzed = await model.analyzeMediaOrganizerItem(
                                source: item.source,
                                destination: destination
                            ) {
                                onAnalyzed(analyzed)

                                let urls = (analyzed.reviewFrames ?? []).compactMap {
                                    model.api.mediaOrganizerFrameURL($0.frameId)
                                }
                                let suggestion = await MediaVisualAnalyzer.analyze(frameURLs: urls)
                                visualSuggestion = suggestion

                                if let title = suggestion.title, !title.isEmpty {
                                    reviewedTitle = title
                                }
                                if let type = suggestion.type {
                                    reviewedType = type
                                }
                            }
                            analyzing = false
                        }
                    } label: {
                        if analyzing {
                            HStack {
                                ProgressView().controlSize(.small)
                                Text("Analyzing…")
                            }
                        } else {
                            Label("Analyze Mystery Clip", systemImage: "film.stack")
                        }
                    }
                    .disabled(analyzing)
                    .padding(.top, 4)
                }

                if let suggestion = visualSuggestion,
                   !suggestion.recognizedText.isEmpty {
                    VStack(alignment: .leading, spacing: 5) {
                        Label("Apple Vision text", systemImage: "text.viewfinder")
                            .font(.caption.bold())
                        Text(suggestion.summary)
                            .font(.caption)
                            .foregroundColor(.secondary)
                            .textSelection(.enabled)

                        if suggestion.title != nil || suggestion.type != nil {
                            Text("Suggestion only — review before approving.")
                                .font(.caption2)
                                .foregroundColor(.secondary)
                        }
                    }
                    .padding(.vertical, 4)
                }

                if item.confidence == "low" || item.reviewed == true {
                    VStack(alignment: .leading, spacing: 8) {
                        TextField("Reviewed title", text: $reviewedTitle)

                        HStack {
                            Picker("Type", selection: $reviewedType) {
                                Text("General").tag("general")
                                Text("Station ID").tag("station-id")
                                Text("Bumper").tag("bumper")
                                Text("Commercial").tag("commercial")
                                Text("Promo").tag("promo")
                            }
                            .frame(maxWidth: 220)

                            Toggle("Reviewed / approve", isOn: $reviewed)
                        }
                    }
                    .padding(.top, 4)
                }
            }

            Spacer()

            if item.action == "unchanged" {
                Text("Already organized")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding(.vertical, 5)
    }
}

struct SchedulesView: View {
    @EnvironmentObject var model: AppModel
    @State private var searchText = ""

    private var filteredSchedules: [ScheduleSummary] {
        let query = searchText.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        guard !query.isEmpty else { return model.schedules }

        return model.schedules.filter { schedule in
            [
                schedule.id,
                schedule.description,
                schedule.playlist,
                schedule.blocks.map { $0.name }.joined(separator: " "),
                schedule.blocks.compactMap { $0.preset }.joined(separator: " ")
            ]
            .joined(separator: " ")
            .lowercased()
            .contains(query)
        }
    }

    var body: some View {
        List(filteredSchedules) { schedule in
            NavigationLink(destination: ScheduleDetailView(schedule: schedule)) {
                HStack(spacing: 14) {
                    Image(systemName: "calendar")
                        .font(.title2)
                        .frame(width: 28)

                    VStack(alignment: .leading, spacing: 4) {
                        HStack {
                            Text(schedule.id.replacingOccurrences(of: "-", with: " ").capitalized)
                                .font(.headline)
                            if matchingAutomation(schedule)?.loaded == true {
                                StatusBadge(text: "Automated", good: true)
                            }
                        }
                        Text(schedule.description)
                            .font(.caption)
                            .foregroundColor(.secondary)
                            .lineLimit(1)
                        Text(schedule.blocks.map { $0.name }.joined(separator: "  •  "))
                            .font(.caption2)
                            .foregroundColor(.secondary)
                            .lineLimit(1)
                    }

                    Spacer()

                    VStack(alignment: .trailing, spacing: 3) {
                        Text(duration(schedule.totalMinutes))
                        Text("\(schedule.blocks.count) blocks")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
                .padding(.vertical, 5)
            }
        }
        .navigationTitle("Schedules")
        .searchable(text: $searchText, prompt: "Search schedules or blocks")
        .toolbar {
            Button("Reload") {
                Task {
                    await model.loadSchedules()
                    await model.loadAutomation()
                }
            }
        }
        .task {
            async let schedules: Void = model.loadSchedules()
            async let automation: Void = model.loadAutomation()
            _ = await (schedules, automation)
        }
    }

    private func matchingAutomation(_ schedule: ScheduleSummary) -> AutomationJob? {
        model.automationJobs.first { $0.name == schedule.id }
    }

    private func duration(_ minutes: Int) -> String {
        let hours = minutes / 60
        let remainder = minutes % 60
        if hours == 0 { return "\(remainder)m" }
        if remainder == 0 { return "\(hours)h" }
        return "\(hours)h \(remainder)m"
    }
}

struct ScheduleDetailView: View {
    @EnvironmentObject var model: AppModel
    let schedule: ScheduleSummary

    @State private var playlistName: String
    @State private var replaceExisting = true
    @State private var avoidRecent = 150
    @State private var minShowGap = 2
    @State private var seasonal = "auto"
    @State private var specialEvery = 8
    @State private var unwatched = false
    @State private var followWatchProgress = true
    @State private var preview: SchedulePreviewResponse?
    @State private var isLoading = false
    @State private var confirmBuild = false

    init(schedule: ScheduleSummary) {
        self.schedule = schedule
        _playlistName = State(initialValue: schedule.playlist)
    }

    private let columns = [
        GridItem(.adaptive(minimum: 190, maximum: 240), spacing: 18)
    ]

    var body: some View {
        HSplitView {
            ScrollView {
                VStack(alignment: .leading, spacing: 18) {
                    VStack(alignment: .leading, spacing: 5) {
                        Text(schedule.id.replacingOccurrences(of: "-", with: " ").capitalized)
                            .font(.title.bold())
                        Text(schedule.description)
                            .foregroundColor(.secondary)

                        HStack(spacing: 12) {
                            Label(duration(schedule.totalMinutes), systemImage: "clock")
                            Label("\(schedule.blocks.count) blocks", systemImage: "square.stack.3d.up")
                            if automationJob?.loaded == true {
                                StatusBadge(text: "Automation loaded", good: true)
                            } else if automationJob != nil {
                                StatusBadge(text: "Automation not loaded", good: false)
                            }
                        }
                        .font(.caption)
                    }

                    GroupBox("Programming Blocks") {
                        VStack(spacing: 0) {
                            ForEach(Array(schedule.blocks.enumerated()), id: \.element.id) { offset, block in
                                ScheduleTimelineRow(
                                    block: block,
                                    startMinute: startMinute(for: offset)
                                )
                                if offset < schedule.blocks.count - 1 {
                                    Divider().padding(.leading, 60)
                                }
                            }
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                    }

                    GroupBox("Build Options") {
                        VStack(alignment: .leading, spacing: 10) {
                            TextField("Plex playlist", text: $playlistName)
                            Toggle("Replace existing playlist", isOn: $replaceExisting)
                            Toggle("Prefer unwatched episodes", isOn: $unwatched)
                            Toggle("Follow Plex watch progress", isOn: $followWatchProgress)

                            Stepper(
                                "Avoid recent episodes: \(avoidRecent)",
                                value: $avoidRecent,
                                in: 0...10000,
                                step: 10
                            )
                            Stepper(
                                "Minimum show gap: \(minShowGap)",
                                value: $minShowGap,
                                in: 0...20
                            )
                            Stepper(
                                "Seasonal special frequency: \(specialEvery)",
                                value: $specialEvery,
                                in: 1...50
                            )

                            Picker("Seasonal mode", selection: $seasonal) {
                                Text("Automatic").tag("auto")
                                Text("None").tag("none")
                                Text("Halloween").tag("halloween")
                                Text("Christmas").tag("christmas")
                            }

                            HStack {
                                Button("Preview Lineup") {
                                    Task { await loadPreview() }
                                }
                                Button(replaceExisting ? "Build / Replace Now" : "Build Now") {
                                    confirmBuild = true
                                }
                            }

                            Text("Clock-time automation is managed in the Automation screen. Preview is read-only; Build generates a fresh lineup using these settings.")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                    }
                }
                .padding(20)
            }
            .frame(minWidth: 380, idealWidth: 440)

            Group {
                if isLoading {
                    ProgressView("Programming lineup…")
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if let preview {
                    ScrollView {
                        VStack(alignment: .leading, spacing: 14) {
                            HStack {
                                Text("Preview")
                                    .font(.title2.bold())
                                Spacer()
                                Text("\(preview.itemCount) items")
                                    .foregroundColor(.secondary)
                            }

                            ForEach(preview.blocks) { block in
                                GroupBox {
                                    LazyVGrid(columns: columns, alignment: .leading, spacing: 16) {
                                        ForEach(block.items) { item in
                                            PlaylistMediaCard(item: item)
                                        }
                                    }
                                } label: {
                                    HStack {
                                        Text(block.name)
                                        Spacer()
                                        Text("\(block.minutes) min • \(block.itemCount) items")
                                            .foregroundColor(.secondary)
                                    }
                                }
                            }
                        }
                        .padding(20)
                    }
                } else {
                    VStack(spacing: 10) {
                        Image(systemName: "calendar.badge.clock")
                            .font(.system(size: 42))
                            .foregroundColor(.secondary)
                        Text("Preview the programmed lineup before building it.")
                            .foregroundColor(.secondary)
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                }
            }
            .frame(minWidth: 520)
        }
        .navigationTitle(schedule.playlist)
        .alert(isPresented: $confirmBuild) {
            Alert(
                title: Text(replaceExisting ? "Build and replace playlist?" : "Build playlist?"),
                message: Text("A fresh \(duration(schedule.totalMinutes)) lineup will be programmed into \(playlistName)."),
                primaryButton: .default(Text("Build Now")) {
                    Task { await buildNow() }
                },
                secondaryButton: .cancel()
            )
        }
    }

    private var automationJob: AutomationJob? {
        model.automationJobs.first { $0.name == schedule.id }
    }

    private func startMinute(for index: Int) -> Int {
        schedule.blocks.prefix(index).reduce(0) { $0 + $1.minutes }
    }

    private func duration(_ minutes: Int) -> String {
        let hours = minutes / 60
        let remainder = minutes % 60
        if hours == 0 { return "\(remainder)m" }
        if remainder == 0 { return "\(hours)h" }
        return "\(hours)h \(remainder)m"
    }

    private func clockOffset(_ minute: Int) -> String {
        let hours = minute / 60
        let minutes = minute % 60
        return String(format: "+%d:%02d", hours, minutes)
    }

    private func optionsRequest() -> ScheduleOptionsRequest {
        ScheduleOptionsRequest(
            playlist: playlistName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
                ? nil
                : playlistName.trimmingCharacters(in: .whitespacesAndNewlines),
            avoidRecent: avoidRecent,
            minShowGap: minShowGap,
            seasonal: seasonal,
            specialEvery: specialEvery,
            unwatched: unwatched,
            ignoreWatchProgress: !followWatchProgress
        )
    }

    private func loadPreview() async {
        isLoading = true
        defer { isLoading = false }
        do {
            preview = try await model.api.schedulePreview(
                id: schedule.id,
                request: optionsRequest()
            )
            model.error = nil
        } catch {
            model.error = error.localizedDescription
        }
    }

    private func buildNow() async {
        let options = optionsRequest()
        let request = ScheduleBuildRequest(
            playlist: options.playlist,
            avoidRecent: options.avoidRecent,
            minShowGap: options.minShowGap,
            seasonal: options.seasonal,
            specialEvery: options.specialEvery,
            unwatched: options.unwatched,
            ignoreWatchProgress: options.ignoreWatchProgress,
            replace: replaceExisting
        )

        isLoading = true
        defer { isLoading = false }

        do {
            let response = try await model.api.buildSchedule(
                id: schedule.id,
                request: request
            )
            model.message = "Built \(response.playlist) with \(response.itemCount) items."
            NotificationManager.shared.send(
                title: "Plex Curator Schedule",
                body: "Built \(response.playlist) with \(response.itemCount) items."
            )
            await model.loadPlaylists()
            preview = nil
            model.error = nil
        } catch {
            model.error = error.localizedDescription
        }
    }
}

struct ScheduleTimelineRow: View {
    let block: ScheduleBlockDefinition
    let startMinute: Int

    var body: some View {
        HStack(alignment: .center, spacing: 12) {
            Text(offset)
                .font(.system(.caption, design: .monospaced))
                .foregroundColor(.secondary)
                .frame(width: 52, alignment: .trailing)

            RoundedRectangle(cornerRadius: 6)
                .fill(Color.accentColor.opacity(0.16))
                .frame(width: 8, height: max(36, CGFloat(block.minutes) * 0.55))

            VStack(alignment: .leading, spacing: 3) {
                Text(block.name)
                    .font(.headline)
                HStack(spacing: 8) {
                    Text(block.type?.capitalized ?? "Block")
                    if let preset = block.preset {
                        Text(preset)
                    }
                    Text("\(block.minutes) min")
                    if let seasonal = block.seasonal {
                        Text(seasonal.capitalized)
                    }
                }
                .font(.caption)
                .foregroundColor(.secondary)
            }

            Spacer()
        }
        .padding(.vertical, 6)
    }

    private var offset: String {
        let hours = startMinute / 60
        let minutes = startMinute % 60
        return String(format: "+%d:%02d", hours, minutes)
    }
}

struct PlaylistsView: View {
    @EnvironmentObject var model: AppModel
    @State private var searchText = ""

    private var filteredPlaylists: [PlaylistSummary] {
        let query = searchText.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        guard !query.isEmpty else { return model.playlists }
        return model.playlists.filter {
            $0.title.lowercased().contains(query)
            || ($0.playlistType ?? "").lowercased().contains(query)
        }
    }

    var body: some View {
        List(filteredPlaylists) { playlist in
            NavigationLink(destination: PlaylistDetailView(playlist: playlist)) {
                HStack(spacing: 12) {
                    Image(systemName: playlist.smart ? "sparkles.rectangle.stack" : "rectangle.stack")
                        .font(.title2)
                        .frame(width: 28)
                    VStack(alignment: .leading, spacing: 3) {
                        Text(playlist.title).font(.headline)
                        HStack(spacing: 8) {
                            Text("\(playlist.itemCount ?? 0) items")
                            if let type = playlist.playlistType {
                                Text(type.capitalized)
                            }
                            if playlist.smart {
                                Text("Smart")
                            }
                        }
                        .font(.caption)
                        .foregroundColor(.secondary)
                    }
                    Spacer()
                }
                .padding(.vertical, 4)
            }
        }
        .navigationTitle("Playlists")
        .searchable(text: $searchText, prompt: "Search playlists")
        .toolbar {
            Button("Reload") { Task { await model.loadPlaylists() } }
        }
        .task {
            if model.playlists.isEmpty {
                await model.loadPlaylists()
            }
        }
    }
}

struct PlaylistDetailView: View {
    @EnvironmentObject var model: AppModel
    let playlist: PlaylistSummary

    @State private var detail: PlaylistDetailResponse?
    @State private var searchText = ""
    @State private var isLoading = false

    private var filteredItems: [MediaItem] {
        guard let items = detail?.items else { return [] }
        let query = searchText.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        guard !query.isEmpty else { return items }
        return items.filter { item in
            [
                item.title ?? "",
                item.showTitle ?? "",
                item.summary ?? "",
                item.contentRating ?? "",
                item.year.map(String.init) ?? ""
            ]
            .joined(separator: " ")
            .lowercased()
            .contains(query)
        }
    }

    private let columns = [
        GridItem(.adaptive(minimum: 190, maximum: 240), spacing: 18)
    ]

    var body: some View {
        Group {
            if isLoading && detail == nil {
                ProgressView("Loading playlist…")
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if let detail {
                ScrollView {
                    LazyVGrid(columns: columns, alignment: .leading, spacing: 20) {
                        ForEach(filteredItems) { item in
                            PlaylistMediaCard(item: item)
                        }
                    }
                    .padding(20)
                }
                .searchable(text: $searchText, prompt: "Search this playlist")
                .overlay(alignment: .topTrailing) {
                    Text("\(detail.itemCount) items")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .padding(12)
                }
            } else {
                VStack(spacing: 12) {
                    Text("Playlist could not be loaded.")
                    Button("Retry") { Task { await load() } }
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
        }
        .navigationTitle(playlist.title)
        .toolbar {
            Button("Reload") { Task { await load() } }
        }
        .task { await load() }
    }

    private func load() async {
        isLoading = true
        defer { isLoading = false }
        do {
            detail = try await model.api.playlistDetail(name: playlist.title)
            model.error = nil
        } catch {
            model.error = error.localizedDescription
        }
    }
}

struct PlaylistMediaCard: View {
    @EnvironmentObject var model: AppModel
    let item: MediaItem

    private var artworkHeight: CGFloat {
        item.type == "episode" ? 120 : 260
    }

    private var artworkWidth: Int {
        item.type == "episode" ? 360 : 240
    }

    private var requestedHeight: Int {
        item.type == "episode" ? 203 : 360
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            ZStack {
                RoundedRectangle(cornerRadius: 9)
                    .fill(Color.secondary.opacity(0.12))

                if item.thumbAvailable == true,
                   let url = model.api.artworkURL(
                    ratingKey: item.ratingKey,
                    width: artworkWidth,
                    height: requestedHeight
                   ) {
                    AsyncImage(url: url) { phase in
                        switch phase {
                        case .empty:
                            ProgressView()
                        case .success(let image):
                            image
                                .resizable()
                                .scaledToFill()
                        case .failure:
                            Image(systemName: item.type == "episode" ? "tv" : "film")
                                .font(.largeTitle)
                                .foregroundColor(.secondary)
                        @unknown default:
                            EmptyView()
                        }
                    }
                } else {
                    Image(systemName: item.type == "episode" ? "tv" : "film")
                        .font(.largeTitle)
                        .foregroundColor(.secondary)
                }
            }
            .frame(maxWidth: .infinity)
            .frame(height: artworkHeight)
            .clipShape(RoundedRectangle(cornerRadius: 9))

            Text(item.displayTitle)
                .font(.headline)
                .lineLimit(2)

            HStack(spacing: 6) {
                if let rating = item.contentRating, !rating.isEmpty {
                    Text(rating)
                }
                if let minutes = item.durationMinutes {
                    Text("\(minutes) min")
                }
                if item.watched {
                    Image(systemName: "checkmark.circle.fill")
                        .help("Watched")
                }
            }
            .font(.caption)
            .foregroundColor(.secondary)

            if let summary = item.summary, !summary.isEmpty {
                Text(summary)
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .lineLimit(3)
            }
        }
        .padding(10)
        .background(Color.secondary.opacity(0.06))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }
}

struct MovieCuratorView: View {
    @EnvironmentObject var model: AppModel

    @State private var genre = ""
    @State private var yearMin = ""
    @State private var yearMax = ""
    @State private var maxRuntime = ""
    @State private var contentRatings = ""
    @State private var minAudience = ""
    @State private var minCritic = ""
    @State private var watchMode = 0
    @State private var randomize = false
    @State private var limit = 50
    @State private var playlistName = "Curated Movies"
    @State private var replaceExisting = true
    @State private var previewItems: [MediaItem] = []
    @State private var isLoading = false
    @State private var validationMessage: String?
    @State private var confirmCreate = false

    private let columns = [
        GridItem(.adaptive(minimum: 190, maximum: 240), spacing: 18)
    ]

    var body: some View {
        HSplitView {
            Form {
                Section("Filters") {
                    TextField("Genre", text: $genre)
                    HStack {
                        TextField("Year minimum", text: $yearMin)
                        TextField("Year maximum", text: $yearMax)
                    }
                    TextField("Maximum runtime (minutes)", text: $maxRuntime)
                    TextField("Content ratings (G, PG, PG-13)", text: $contentRatings)
                    TextField("Minimum audience rating (0–10)", text: $minAudience)
                    TextField("Minimum critic rating (0–10)", text: $minCritic)

                    Picker("Watch state", selection: $watchMode) {
                        Text("Any").tag(0)
                        Text("Unwatched").tag(1)
                        Text("Watched").tag(2)
                    }

                    Toggle("Randomize results", isOn: $randomize)
                    Stepper("Limit: \(limit)", value: $limit, in: 1...500)
                }

                Section("Playlist") {
                    TextField("Playlist name", text: $playlistName)
                    Toggle("Replace existing playlist", isOn: $replaceExisting)
                }

                if let validationMessage {
                    Section {
                        Text(validationMessage)
                            .foregroundColor(.red)
                    }
                }

                Section {
                    HStack {
                        Button("Preview") { Task { await preview() } }
                        Button(replaceExisting ? "Create / Replace" : "Create") {
                            if validate() {
                                confirmCreate = true
                            }
                        }
                        .disabled(previewItems.isEmpty)
                    }
                }
            }
            .frame(minWidth: 320, idealWidth: 360, maxWidth: 420)

            Group {
                if isLoading {
                    ProgressView("Filtering movies…")
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if previewItems.isEmpty {
                    VStack(spacing: 10) {
                        Image(systemName: "film.stack")
                            .font(.system(size: 42))
                            .foregroundColor(.secondary)
                        Text("Choose filters and preview your movie lineup.")
                            .foregroundColor(.secondary)
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else {
                    ScrollView {
                        LazyVGrid(columns: columns, alignment: .leading, spacing: 20) {
                            ForEach(previewItems) { item in
                                PlaylistMediaCard(item: item)
                            }
                        }
                        .padding(20)
                    }
                }
            }
            .frame(minWidth: 500)
        }
        .navigationTitle("Movie Curator")
        .alert(isPresented: $confirmCreate) {
            Alert(
                title: Text(replaceExisting ? "Create or replace playlist?" : "Create playlist?"),
                message: Text("\(playlistName) will contain \(previewItems.count) movies."),
                primaryButton: .default(Text("Continue")) {
                    Task { await createPlaylist() }
                },
                secondaryButton: .cancel()
            )
        }
    }

    private func parseInt(_ value: String, label: String) -> Int? {
        let trimmed = value.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return nil }
        guard let parsed = Int(trimmed) else {
            validationMessage = "\(label) must be a whole number."
            return nil
        }
        return parsed
    }

    private func parseDouble(_ value: String, label: String) -> Double? {
        let trimmed = value.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return nil }
        guard let parsed = Double(trimmed) else {
            validationMessage = "\(label) must be a number."
            return nil
        }
        return parsed
    }

    private func validate() -> Bool {
        validationMessage = nil
        guard !playlistName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            validationMessage = "Playlist name is required."
            return false
        }

        let minYear = parseInt(yearMin, label: "Minimum year")
        if validationMessage != nil { return false }
        let maxYear = parseInt(yearMax, label: "Maximum year")
        if validationMessage != nil { return false }
        _ = parseInt(maxRuntime, label: "Maximum runtime")
        if validationMessage != nil { return false }
        let audience = parseDouble(minAudience, label: "Audience rating")
        if validationMessage != nil { return false }
        let critic = parseDouble(minCritic, label: "Critic rating")
        if validationMessage != nil { return false }

        if let minYear, let maxYear, minYear > maxYear {
            validationMessage = "Minimum year cannot be greater than maximum year."
            return false
        }
        if let audience, !(0...10).contains(audience) {
            validationMessage = "Audience rating must be between 0 and 10."
            return false
        }
        if let critic, !(0...10).contains(critic) {
            validationMessage = "Critic rating must be between 0 and 10."
            return false
        }
        return true
    }

    private func ratings() -> [String] {
        contentRatings
            .split(separator: ",")
            .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }
    }

    private func filterRequest() -> MovieFilterRequest? {
        validationMessage = nil
        let minYear = parseInt(yearMin, label: "Minimum year")
        if validationMessage != nil { return nil }
        let maxYear = parseInt(yearMax, label: "Maximum year")
        if validationMessage != nil { return nil }
        let runtime = parseInt(maxRuntime, label: "Maximum runtime")
        if validationMessage != nil { return nil }
        let audience = parseDouble(minAudience, label: "Audience rating")
        if validationMessage != nil { return nil }
        let critic = parseDouble(minCritic, label: "Critic rating")
        if validationMessage != nil { return nil }

        if let minYear, let maxYear, minYear > maxYear {
            validationMessage = "Minimum year cannot be greater than maximum year."
            return nil
        }

        return MovieFilterRequest(
            library: "Movies",
            genre: genre.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? nil : genre,
            yearMin: minYear,
            yearMax: maxYear,
            maxRuntime: runtime,
            contentRatings: ratings(),
            minAudience: audience,
            minCritic: critic,
            watched: watchMode == 2,
            unwatched: watchMode == 1,
            random: randomize,
            limit: limit
        )
    }

    private func preview() async {
        guard let request = filterRequest() else { return }
        isLoading = true
        defer { isLoading = false }
        do {
            let response = try await model.api.moviePreview(request)
            previewItems = response.items
            model.message = "Movie preview found \(response.count) matches."
            model.error = nil
        } catch {
            model.error = error.localizedDescription
        }
    }

    private func createPlaylist() async {
        guard validate(), let filter = filterRequest() else { return }

        let request = MoviePlaylistRequest(
            library: filter.library,
            genre: filter.genre,
            yearMin: filter.yearMin,
            yearMax: filter.yearMax,
            maxRuntime: filter.maxRuntime,
            contentRatings: filter.contentRatings,
            minAudience: filter.minAudience,
            minCritic: filter.minCritic,
            watched: filter.watched,
            unwatched: filter.unwatched,
            random: filter.random,
            limit: filter.limit,
            playlist: playlistName.trimmingCharacters(in: .whitespacesAndNewlines),
            replace: replaceExisting
        )

        do {
            let response = try await model.api.createMoviePlaylist(request)
            model.message = "Created \(response.playlist) with \(response.itemCount) movies."
            NotificationManager.shared.send(
                title: "Plex Curator",
                body: "Created \(response.playlist) with \(response.itemCount) movies."
            )
            await model.loadPlaylists()
            model.error = nil
        } catch {
            model.error = error.localizedDescription
        }
    }
}

struct KidsScaryWishlistView: View {
    @EnvironmentObject var model: AppModel

    @State private var response: WishlistResponse?
    @State private var searchText = ""
    @State private var filter = 0
    @State private var isLoading = false

    private var filteredEntries: [WishlistEntry] {
        guard let entries = response?.entries else { return [] }
        let query = searchText.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()

        return entries.filter { entry in
            let statusMatches: Bool
            switch filter {
            case 1: statusMatches = !entry.found
            case 2: statusMatches = entry.found
            default: statusMatches = true
            }

            guard statusMatches else { return false }
            guard !query.isEmpty else { return true }

            return [
                entry.requestedTitle,
                entry.matchedTitle ?? "",
                entry.requestedYear.map(String.init) ?? ""
            ]
            .joined(separator: " ")
            .lowercased()
            .contains(query)
        }
    }

    var body: some View {
        VStack(spacing: 0) {
            if let response {
                HStack(spacing: 18) {
                    metric("FOUND", response.foundCount)
                    metric("MISSING", response.missingCount)
                    metric("TOTAL", response.totalCount)
                    Spacer()
                    Button("Reload") { Task { await load() } }
                }
                .padding()
                Divider()
            }

            if isLoading && response == nil {
                ProgressView("Checking Plex library…")
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                List(filteredEntries) { entry in
                    WishlistRow(entry: entry)
                }
            }
        }
        .navigationTitle("Kids Scary Wishlist")
        .searchable(text: $searchText, prompt: "Search wishlist")
        .toolbar {
            Picker("Status", selection: $filter) {
                Text("All").tag(0)
                Text("Missing").tag(1)
                Text("Found").tag(2)
            }
            .pickerStyle(SegmentedPickerStyle())
            .frame(width: 230)
        }
        .task { await load() }
    }

    private func metric(_ label: String, _ value: Int) -> some View {
        VStack {
            Text("\(value)").font(.title2.bold())
            Text(label).font(.caption).foregroundColor(.secondary)
        }
    }

    private func load() async {
        isLoading = true
        defer { isLoading = false }
        do {
            response = try await model.api.kidsScaryWishlist()
            model.error = nil
        } catch {
            model.error = error.localizedDescription
        }
    }
}

struct WishlistRow: View {
    @EnvironmentObject var model: AppModel
    let entry: WishlistEntry

    var body: some View {
        HStack(spacing: 12) {
            if let item = entry.item,
               item.thumbAvailable == true,
               let url = model.api.artworkURL(ratingKey: item.ratingKey, width: 90, height: 135) {
                AsyncImage(url: url) { phase in
                    switch phase {
                    case .success(let image):
                        image.resizable().scaledToFill()
                    case .empty:
                        ProgressView()
                    default:
                        Image(systemName: "film")
                            .foregroundColor(.secondary)
                    }
                }
                .frame(width: 60, height: 90)
                .clipShape(RoundedRectangle(cornerRadius: 6))
            } else {
                ZStack {
                    RoundedRectangle(cornerRadius: 6)
                        .fill(Color.secondary.opacity(0.1))
                    Image(systemName: "film")
                        .foregroundColor(.secondary)
                }
                .frame(width: 60, height: 90)
            }

            Image(systemName: entry.found ? "checkmark.circle.fill" : "xmark.circle")
                .foregroundColor(entry.found ? .green : .orange)

            VStack(alignment: .leading, spacing: 3) {
                Text(entry.requestedTitle)
                    .font(.headline)

                HStack {
                    if let year = entry.requestedYear {
                        Text(String(year))
                    }
                    if let matched = entry.matchedTitle,
                       matched.caseInsensitiveCompare(entry.requestedTitle) != .orderedSame {
                        Text("Matched: \(matched)")
                    }
                }
                .font(.caption)
                .foregroundColor(.secondary)
            }

            Spacer()

            Text(entry.found ? "In Plex" : "Missing")
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding(.vertical, 4)
    }
}

struct HistoryView: View {
    @EnvironmentObject var model: AppModel
    @State private var searchText = ""

    private var filteredHistory: [HistoryItem] {
        let query = searchText.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        guard !query.isEmpty else { return model.history }
        return model.history.filter { item in
            [
                item.showTitle,
                item.episodeTitle,
                item.channelName,
                "S\(String(format: "%02d", item.seasonNumber))E\(String(format: "%02d", item.episodeNumber))"
            ]
            .joined(separator: " ")
            .lowercased()
            .contains(query)
        }
    }

    var body: some View {
        List(filteredHistory) { item in
            HStack {
                VStack(alignment: .leading) {
                    Text("\(item.showTitle) S\(String(format: "%02d", item.seasonNumber))E\(String(format: "%02d", item.episodeNumber)) — \(item.episodeTitle)")
                    Text(item.channelName).font(.caption).foregroundColor(.secondary)
                }
                Spacer()
                Text(item.displayDate)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            .padding(.vertical, 3)
        }
        .navigationTitle("History")
        .searchable(text: $searchText, prompt: "Search show, episode, or station")
        .toolbar {
            Button("Reload") { Task { await model.loadHistory() } }
        }
        .task { await model.loadHistory() }
    }
}

struct HealthView: View {
    @EnvironmentObject var model: AppModel
    var body: some View {
        List(model.doctor?.checks ?? []) { check in
            HStack(alignment: .top) {
                Image(systemName: check.status == "PASS" ? "checkmark.circle.fill" : "exclamationmark.triangle.fill")
                    .foregroundColor(check.status == "PASS" ? .green : .orange)
                VStack(alignment: .leading) {
                    Text(check.label)
                    Text(check.detail).font(.caption).foregroundColor(.secondary)
                }
            }
        }.navigationTitle("Health")
    }
}

struct AutomationView: View {
    @EnvironmentObject var model: AppModel
    @State private var confirmJob: AutomationJob?
    @State private var confirmAction: String?

    var body: some View {
        VStack(spacing: 0) {
            HStack {
                VStack(alignment: .leading, spacing: 3) {
                    Text("Automation").font(.title.bold())
                    Text("Manage Plex Curator LaunchAgents")
                        .foregroundColor(.secondary)
                }
                Spacer()
                Button("Reload") { Task { await model.loadAutomation() } }
            }
            .padding()

            Divider()

            List(model.automationJobs) { job in
                HStack(alignment: .center, spacing: 14) {
                    Image(systemName: job.loaded ? "checkmark.circle.fill" : "circle")
                        .foregroundColor(job.loaded ? .green : .secondary)

                    VStack(alignment: .leading, spacing: 3) {
                        HStack {
                            Text(job.name).font(.headline)
                            if job.protected {
                                Text("Protected")
                                    .font(.caption2)
                                    .padding(.horizontal, 6)
                                    .padding(.vertical, 2)
                                    .background(Color.secondary.opacity(0.15))
                                    .clipShape(Capsule())
                            }
                        }
                        Text(job.description)
                            .font(.caption)
                            .foregroundColor(.secondary)
                        HStack(spacing: 10) {
                            Text(job.loaded ? "Loaded" : "Not loaded")
                            if let state = job.state { Text("State: \(state)") }
                            if let exit = job.lastExitCode { Text("Last exit: \(exit)") }
                            if let runs = job.runs { Text("Runs: \(runs)") }
                        }
                        .font(.caption2)
                        .foregroundColor(.secondary)
                    }

                    Spacer()

                    Button("Run Now") {
                        confirmAction = "run-now"
                        confirmJob = job
                    }
                    .disabled(job.protected && job.name == "api-server")

                    if job.loaded || job.plistExists {
                        Button("Remove") {
                            confirmAction = "uninstall"
                            confirmJob = job
                        }
                        .disabled(job.protected)
                    } else {
                        Button("Install") {
                            confirmAction = "install"
                            confirmJob = job
                        }
                    }
                }
                .padding(.vertical, 5)
            }
        }
        .navigationTitle("Automation")
        .task { await model.loadAutomation() }
        .alert(item: $confirmJob) { job in
            let action = confirmAction ?? ""
            let title: String
            let message: String
            switch action {
            case "install":
                title = "Install \(job.name)?"
                message = "This will install and load its LaunchAgent."
            case "uninstall":
                title = "Remove \(job.name)?"
                message = "This will unload the LaunchAgent and remove its plist."
            default:
                title = "Run \(job.name) now?"
                message = "This will trigger the automation immediately."
            }
            return Alert(
                title: Text(title),
                message: Text(message),
                primaryButton: .default(Text("Continue")) {
                    Task { await model.automationAction(job, action: action) }
                },
                secondaryButton: .cancel()
            )
        }
    }
}

struct LogsView: View {
    @EnvironmentObject var model: AppModel
    @State private var job = "api-server"
    @State private var errors = false

    var body: some View {
        VStack(spacing: 0) {
            HStack {
                TextField("Job", text: $job).textFieldStyle(RoundedBorderTextFieldStyle()).frame(width: 220)
                Toggle("Errors", isOn: $errors)
                Button("Load") { Task { await model.loadLogs(job: job, errors: errors) } }
                Spacer()
            }.padding()
            Divider()
            ScrollView([.vertical, .horizontal]) {
                Text(model.log?.lines.joined(separator: "\n") ?? "No log loaded.")
                    .font(.system(.body, design: .monospaced))
                    .textSelection(.enabled)
                    .frame(maxWidth: .infinity, alignment: .topLeading)
                    .padding()
            }
        }.navigationTitle("Logs")
    }
}

struct SettingsView: View {
    @EnvironmentObject var model: AppModel

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text("Local API").font(.title2.bold())
            setting("Address", "http://127.0.0.1:8765")
            setting("API key", model.api.apiKeyPath)
            setting("Exposure", "localhost only")
            setting("CORS", "disabled")
            Divider()
            Text("Backend").font(.title2.bold())
            setting("Curator", model.status.map { "v\($0.curatorVersion)" } ?? "Unavailable")
            setting("API", model.status.map { "v\($0.apiVersion)" } ?? "Unavailable")
            Spacer()
        }.padding(24).navigationTitle("Settings")
    }

    private func setting(_ label: String, _ value: String) -> some View {
        HStack(alignment: .top) {
            Text(label).foregroundColor(.secondary).frame(width: 100, alignment: .leading)
            Text(value).textSelection(.enabled)
            Spacer()
        }
    }
}