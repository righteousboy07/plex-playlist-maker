import SwiftUI
import Foundation
import UserNotifications

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
    let interstitialEvery: Int
    let interstitialCount: Int
    let unwatched: Bool
    let syncWatchProgress: Bool
    let includeShows: [String]
    let excludeShows: [String]
}

struct StationsResponse: Codable { let stations: [Station] }

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

struct PreviewResponse: Codable {
    let station: Station
    let showCount: Int
    let seasonalMode: String
    let itemCount: Int
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
    let interstitialEvery: Int
    let interstitialCount: Int
    let unwatched: Bool
    let syncWatchProgress: Bool
    let includeShows: [String]
    let excludeShows: [String]

    enum CodingKeys: String, CodingKey {
        case name, description, enabled, playlist, preset
        case yearMin, yearMax, kidsOnly, adult, perShow, total
        case avoidRecent, minShowGap, seasonal, specialEvery
        case interstitialPlaylists, interstitialEvery, interstitialCount
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
        try c.encode(interstitialEvery, forKey: .interstitialEvery)
        try c.encode(interstitialCount, forKey: .interstitialCount)
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
        authenticated: Bool = false
    ) async throws -> T {
        guard let url = URL(string: path, relativeTo: baseURL) else {
            throw APIClientError.invalidResponse
        }
        var req = URLRequest(url: url)
        req.httpMethod = method
        req.timeoutInterval = 30
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

    func kidsScaryWishlist() async throws -> WishlistResponse {
        try await request("/api/v1/wishlist/kids-scary")
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
        }
    }
}

struct StationDetailView: View {
    @EnvironmentObject var model: AppModel
    @State private var station: Station
    @State private var tab = 0
    @State private var confirmRefresh = false
    @State private var showEditor = false

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
                Button("Preview") { tab = 1; Task { await model.loadPreview(station) } }
                Button("Diff") { tab = 2; Task { await model.loadDiff(station) } }
                Button("Dry Run") { Task { await model.dryRun(station) } }
                Button("Refresh") { confirmRefresh = true }.disabled(!station.enabled)
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
                List(p.items) { item in Text(item.displayTitle) }
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
    @State private var interstitialEvery: Int
    @State private var interstitialCount: Int
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
        _interstitialPlaylists = State(initialValue: Set(station.interstitialPlaylists))
        _interstitialEvery = State(initialValue: station.interstitialEvery)
        _interstitialCount = State(initialValue: station.interstitialCount)
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
                    Stepper("Station length: \(total)", value: $total, in: 1...1000)
                    Stepper("Avoid recent: \(avoidRecent)", value: $avoidRecent, in: 0...100000)
                    Stepper("Minimum show gap: \(minShowGap)", value: $minShowGap, in: 0...100)
                    Stepper("Special every: \(specialEvery)", value: $specialEvery, in: 1...1000)
                }

                Section("Interstitials") {
                    Text("Choose Plex video playlists containing bumpers, station IDs, promos, or commercials.")
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
                            Toggle(
                                "\(plexPlaylist.title)\(plexPlaylist.itemCount.map { " (\($0))" } ?? "")",
                                isOn: Binding(
                                    get: { interstitialPlaylists.contains(plexPlaylist.title) },
                                    set: { selected in
                                        if selected {
                                            interstitialPlaylists.insert(plexPlaylist.title)
                                        } else {
                                            interstitialPlaylists.remove(plexPlaylist.title)
                                        }
                                    }
                                )
                            )
                        }

                        ForEach(configuredButMissingPlaylists, id: \.self) { title in
                            Toggle(
                                "\(title) (not currently found in Plex)",
                                isOn: Binding(
                                    get: { interstitialPlaylists.contains(title) },
                                    set: { selected in
                                        if selected {
                                            interstitialPlaylists.insert(title)
                                        } else {
                                            interstitialPlaylists.remove(title)
                                        }
                                    }
                                )
                            )
                            .foregroundColor(.secondary)
                        }
                    }

                    Stepper(
                        interstitialEvery == 0
                            ? "Break frequency: Off"
                            : "Break every \(interstitialEvery) program items",
                        value: $interstitialEvery,
                        in: 0...1000
                    )
                    Stepper(
                        "Clips per break: \(interstitialCount)",
                        value: $interstitialCount,
                        in: 1...20
                    )
                    .disabled(interstitialEvery == 0)

                    if interstitialPlaylists.isEmpty {
                        Text("Select at least one playlist to use interstitials.")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    } else if interstitialEvery == 0 {
                        Text("Interstitial pools are selected, but insertion is disabled until break frequency is above 0.")
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
            interstitialEvery: interstitialEvery,
            interstitialCount: interstitialCount,
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