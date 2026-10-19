import { StyleSheet, Text, View } from "react-native";

import { useElapsedTime } from "@/hooks/useElapsedTime";
import type { StationRecord } from "@/types/station";

const MAX_STATION_TIME_MS = 60 * 60 * 1000;

type StationProps = {
    station: StationRecord;
    startedAt: number | null;
};

export default function Station({ station, startedAt }: StationProps) {
    const elapsed = useElapsedTime(startedAt);
    const minutes = Math.min(60, Math.floor(Math.min(elapsed, MAX_STATION_TIME_MS) / 60_000));

    return (
        <View style={styles.row} accessibilityLabel={`${station.name}, ${minutes} minutes`}>
            <View style={styles.details}>
                {station.routeCodes?.length ? (
                    <View style={styles.routes}>
                        {station.routeCodes.map((routeCode) => (
                            <View
                                key={routeCode}
                                style={[styles.routeBadge, routeColors[routeCode] ?? styles.routeDefault]}
                            >
                                <Text style={styles.routeText}>{routeCode}</Text>
                            </View>
                        ))}
                    </View>
                ) : null}
                <View style={styles.stationText}>
                    <Text style={styles.name} numberOfLines={1} ellipsizeMode="tail">
                        {station.name}
                    </Text>
                    {station.subtitle ? (
                        <Text style={styles.subtitle} numberOfLines={1} ellipsizeMode="tail">
                            {station.subtitle}
                        </Text>
                    ) : null}
                </View>
            </View>
            <View style={styles.timerPanel}>
                <Text style={styles.timer} accessibilityLiveRegion="polite">
                    {String(minutes).padStart(2, "0")} min
                </Text>
            </View>
        </View>
    );
}

const routeColors: Record<string, object> = {
    M1: stylesRouteBadge("#159f72"),
    M2: stylesRouteBadge("#e5b400"),
    M3: stylesRouteBadge("#d90b36"),
};

function stylesRouteBadge(backgroundColor: string) {
    return { backgroundColor };
}

const styles = StyleSheet.create({
    row: {
        height: 84,
        flexDirection: "row",
        overflow: "hidden",
        borderWidth: 2,
        borderColor: "#ed2224",
        borderRadius: 17,
        backgroundColor: "#ffffff",
    },
    details: {
        flex: 1,
        minWidth: 0,
        flexDirection: "row",
        alignItems: "center",
        gap: 12,
        paddingHorizontal: 12,
    },
    routes: {
        width: 52,
        flexDirection: "row",
        flexWrap: "wrap",
        alignContent: "center",
        justifyContent: "center",
        gap: 4,
    },
    routeBadge: {
        width: 24,
        height: 24,
        alignItems: "center",
        justifyContent: "center",
        borderRadius: 12,
    },
    routeDefault: {
        backgroundColor: "#686868",
    },
    routeText: {
        color: "#ffffff",
        fontSize: 9,
        fontWeight: "700",
    },
    stationText: {
        flex: 1,
        minWidth: 0,
        gap: 2,
    },
    name: {
        color: "#252525",
        fontSize: 16,
        fontWeight: "700",
    },
    subtitle: {
        color: "#777777",
        fontSize: 11,
    },
    timerPanel: {
        width: 116,
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: "#e9282b",
    },
    timer: {
        color: "#ffffff",
        fontSize: 21,
        fontWeight: "700",
        fontVariant: ["tabular-nums"],
    },
});

