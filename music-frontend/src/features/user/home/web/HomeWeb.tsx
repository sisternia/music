import { useEffect, useState } from "react";
import {
  Image,
  Pressable,
  StyleSheet,
  Text,
  View,
  type DimensionValue,
  type GestureResponderEvent,
  type LayoutChangeEvent,
} from "react-native";

import Header from "@/components/layout/Header";
import Navbar from "@/components/layout/Navbar";
import Icon, { type IconName } from "@/components/ui/Icon";


const SONG_LIST = [
  { title: "Autumn Nocturne", artist: "The Aurelia Trio", time: "3:42", duration: 222 },
  { title: "Velvet Rain", artist: "Mira Sol", time: "4:08", duration: 248 },
  { title: "Midnight Pressing", artist: "Northline Quartet", time: "2:57", duration: 177 },
  { title: "Golden Static", artist: "Luna & The Echoes", time: "3:31", duration: 211 },
];

function formatTime(seconds: number) {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);

  return `${mins}:${String(secs).padStart(2, "0")}`;
}

function getVolumeIcon(volume: number): IconName {
  if (volume <= 0) {
    return "volumeMute";
  }

  if (volume < 0.34) {
    return "volumeLow";
  }

  if (volume < 0.67) {
    return "volumeMedium";
  }

  return "volumeHigh";
}

export default function HomeWeb() {
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [volume, setVolume] = useState(0.72);
  const [spinDegrees, setSpinDegrees] = useState(0);
  const [visualizerTick, setVisualizerTick] = useState(0);
  const [timelineWidth, setTimelineWidth] = useState(320);
  const [volumeTrackWidth, setVolumeTrackWidth] = useState(70);

  const selectedSong = SONG_LIST[selectedIndex];
  const progressPercent = `${Math.min((progress / selectedSong.duration) * 100, 100)}%` as DimensionValue;
  const volumePercent = `${volume * 100}%` as DimensionValue;

  useEffect(() => {
    if (!isPlaying) {
      return;
    }

    const timer = setInterval(() => {
      setProgress((current) => {
        if (current >= selectedSong.duration) {
          setIsPlaying(false);
          return selectedSong.duration;
        }

        return current + 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [isPlaying, selectedSong.duration]);

  useEffect(() => {
    if (!isPlaying) {
      return;
    }

    const timer = setInterval(() => {
      setSpinDegrees((current) => (current + 6) % 360);
      setVisualizerTick((current) => current + 1);
    }, 50);

    return () => clearInterval(timer);
  }, [isPlaying]);

  const handleSelectSong = (index: number) => {
    setSelectedIndex(index);
    setProgress(0);
  };

  const handlePrev = () => {
    setSelectedIndex((current) => (current === 0 ? SONG_LIST.length - 1 : current - 1));
    setProgress(0);
  };

  const handleNext = () => {
    setSelectedIndex((current) => (current + 1) % SONG_LIST.length);
    setProgress(0);
  };

  const updateProgressFromEvent = (event: GestureResponderEvent) => {
    const ratio = Math.max(0, Math.min(event.nativeEvent.locationX / timelineWidth, 1));
    setProgress(Math.round(ratio * selectedSong.duration));
  };

  const handleTimelineLayout = (event: LayoutChangeEvent) => {
    setTimelineWidth(event.nativeEvent.layout.width);
  };

  const updateVolumeFromEvent = (event: GestureResponderEvent) => {
    const nextVolume = Math.max(0, Math.min(event.nativeEvent.locationX / volumeTrackWidth, 1));
    setVolume(nextVolume);
  };

  const handleVolumeLayout = (event: LayoutChangeEvent) => {
    setVolumeTrackWidth(event.nativeEvent.layout.width);
  };

  return (
    <View style={styles.screen}>
      <View style={styles.grid} pointerEvents="none" />

      <Header />

      <View style={styles.content}>
        <Navbar />

        <View style={styles.stage}>
          <View style={styles.turntable}>
            <View style={styles.platter}>
              <Image
                source={require("@/assets/images/Music Disc.png")}
                style={[styles.disc, { transform: [{ rotate: `${spinDegrees}deg` }] }]}
                resizeMode="contain"
              />
            </View>
          </View>

          <View style={styles.infoPanel}>
            <Image
              source={require("@/assets/images/Harmony Auralis Logo.png")}
              style={styles.infoLogo}
              resizeMode="contain"
              accessibilityLabel="Harmony Auralis"
            />
            <Text style={styles.badge}>CLASSIC VINYL • 33 RPM</Text>

            <View style={styles.note}>
              <Text style={styles.noteText}>
                Trải nghiệm nghe nhạc như một mâm đĩa thật: chọn album và để âm thanh chạy qua từng rãnh vinyl.
              </Text>
            </View>

            <View style={styles.visualizer}>
              <View style={styles.visualizerHeader}>
                <View style={styles.liveDot} />
                <Text style={styles.visualizerTitle}>
                  PHỔ ÂM TẦN SỐ (REAL-TIME VISUALIZER)
                </Text>
              </View>
              <View style={styles.waveLine}>
                {Array.from({ length: 40 }).map((_, index) => (
                  <View
                    key={index}
                    style={[
                      styles.bar,
                      isPlaying && {
                        height: 8 + ((index * 13 + visualizerTick * 9) % 56),
                        opacity: 0.35 + (((index + visualizerTick) % 5) * 0.12),
                      },
                      index % 5 === 0 && styles.barStrong,
                      index % 7 === 0 && styles.barSoft,
                    ]}
                  />
                ))}
              </View>
            </View>

            <View style={styles.songList}>
              {SONG_LIST.map((song, index) => {
                const active = index === selectedIndex;

                return (
                  <Pressable
                    key={song.title}
                    onPress={() => handleSelectSong(index)}
                    style={({ pressed }) => [
                      styles.songItem,
                      active && styles.songItemActive,
                      pressed && styles.pressed,
                    ]}
                  >
                    <View style={styles.songIndexWrap}>
                      <Text style={[styles.songIndex, active && styles.songIndexActive]}>
                        {active ? "●" : String(index + 1).padStart(2, "0")}
                      </Text>
                    </View>
                    <Image
                      source={require("@/assets/images/Music Disc.png")}
                      style={styles.songThumb}
                      resizeMode="cover"
                    />
                    <View style={styles.songMeta}>
                      <Text style={[styles.listSongTitle, active && styles.listSongTitleActive]}>
                        {song.title}
                      </Text>
                      <Text style={[styles.listSongArtist, active && styles.listSongArtistActive]}>
                        {song.artist}
                      </Text>
                    </View>
                    <Text style={[styles.songTime, active && styles.songTimeActive]}>
                      {song.time}
                    </Text>
                  </Pressable>
                );
              })}
            </View>

            <View style={styles.playerBar}>
              <View style={styles.trackInfo}>
                <Image
                  source={require("@/assets/images/Music Disc.png")}
                  style={[styles.albumArt, { transform: [{ rotate: `${spinDegrees}deg` }] }]}
                  resizeMode="cover"
                />
                <View>
                  <Text style={styles.songTitle}>{selectedSong.title}</Text>
                  <Text style={styles.songArtist}>{selectedSong.artist}</Text>
                </View>
              </View>

              <View style={styles.playerCenter}>
                <View style={styles.playerButtons}>
                  <Pressable onPress={handlePrev} style={styles.iconButton}>
                    <Icon name="previous" size={19} color="#77736b" />
                  </Pressable>
                  <Pressable
                    onPress={() => setIsPlaying((current) => !current)}
                    style={styles.playButton}
                  >
                    <Icon name={isPlaying ? "pause" : "play"} size={19} color="#ffffff" />
                  </Pressable>
                  <Pressable onPress={handleNext} style={styles.iconButton}>
                    <Icon name="next" size={19} color="#77736b" />
                  </Pressable>
                </View>

                <View style={styles.timelineRow}>
                  <Text style={styles.timeText}>{formatTime(progress)}</Text>
                  <View
                    onLayout={handleTimelineLayout}
                    onStartShouldSetResponder={() => true}
                    onMoveShouldSetResponder={() => true}
                    onResponderGrant={updateProgressFromEvent}
                    onResponderMove={updateProgressFromEvent}
                    style={styles.timeline}
                  >
                    <View style={[styles.timelineFill, { width: progressPercent }]}>
                      <View style={styles.timelineKnob} />
                    </View>
                  </View>
                  <Text style={styles.timeText}>{selectedSong.time}</Text>
                </View>
              </View>

              <View style={styles.playerRight}>
                <View style={styles.rpmBadge}>
                  <Icon name="layers" size={13} color="#8f8b83" />
                  <Text style={styles.rpmText}>33 RPM</Text>
                </View>
                <Pressable onPress={() => setVolume((current) => (current > 0 ? 0 : 0.72))}>
                  <Icon name={getVolumeIcon(volume)} size={16} color="#aaa59b" />
                </Pressable>
                <View
                  onLayout={handleVolumeLayout}
                  onStartShouldSetResponder={() => true}
                  onMoveShouldSetResponder={() => true}
                  onResponderGrant={updateVolumeFromEvent}
                  onResponderMove={updateVolumeFromEvent}
                  style={styles.volumeTrack}
                >
                  <View style={[styles.volumeFill, { width: volumePercent }]}>
                    <View style={styles.volumeKnob} />
                  </View>
                </View>
              </View>
            </View>
          </View>
            </View>
        </View>
      </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: "#fcfcfb",
    overflow: "hidden",
  },
  grid: {
    position: "absolute",
    top: 0,
    right: 0,
    bottom: 0,
    left: 0,
    opacity: 0.42,
    backgroundColor: "#fcfcfb",
  },
  content: {
    flex: 1,
    flexDirection: "row",
    overflow: "hidden",
  },
  stage: {
    flex: 1,
    position: "relative",
    overflow: "hidden",
    flexDirection: "row",
    alignItems: "center",
  },
  turntable: {
    width: "52%",
    height: "100%",
    justifyContent: "center",
    overflow: "hidden",
    borderRightWidth: 1,
    borderRightColor: "rgba(238,236,230,0.72)",
  },
  platter: {
    width: 900,
    height: 900,
    borderRadius: 450,
    marginLeft: -450,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "rgba(0,0,0,0.035)",
    shadowColor: "#000",
    shadowOpacity: 0.14,
    shadowRadius: 30,
    shadowOffset: { width: 0, height: 16 },
  },
  disc: {
    width: 830,
    height: 830,
  },
  infoPanel: {
    width: "48%",
    maxWidth: 820,
    paddingHorizontal: 54,
    gap: 18,
  },
  infoLogo: {
    width: 250,
    height: 74,
  },
  badge: {
    alignSelf: "flex-start",
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 8,
    backgroundColor: "#f1f0ec",
    borderWidth: 1,
    borderColor: "#e1ded6",
    color: "#928c82",
    fontSize: 12,
    fontWeight: "900",
  },
  note: {
    width: 770,
    borderWidth: 1,
    borderColor: "#efeee9",
    backgroundColor: "#fff",
    borderRadius: 22,
    padding: 18,
    shadowColor: "#000",
    shadowOpacity: 0.04,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 6 },
  },
  noteText: {
    width: 734,
    color: "#6f6a60",
    fontSize: 13,
    lineHeight: 20,
    fontStyle: "italic",
  },
  visualizer: {
    width: 770,
    minHeight: 200,
    borderRadius: 22,
    borderWidth: 1,
    borderColor: "#efeee9",
    backgroundColor: "#fff",
    paddingHorizontal: 18,
    paddingTop: 18,
    paddingBottom: 20,
    justifyContent: "space-between",
    shadowColor: "#000",
    shadowOpacity: 0.06,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 4 },
  },
  visualizerHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  liveDot: {
    width: 7,
    height: 7,
    borderRadius: 4,
    backgroundColor: "#24c68a",
  },
  visualizerTitle: {
    color: "#9c9a96",
    fontSize: 10,
    lineHeight: 12,
    fontWeight: "900",
  },
  waveLine: {
    height: 72,
    flexDirection: "row",
    alignItems: "flex-end",
    gap: 6,
  },
  bar: {
    flex: 1,
    height: 2,
    borderRadius: 2,
    backgroundColor: "#b9b8b3",
  },
  barStrong: {
    backgroundColor: "#7f7d78",
  },
  barSoft: {
    backgroundColor: "#d2d1cc",
  },
  songList: {
    width: 770,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: "#efeee9",
    backgroundColor: "rgba(255,255,255,0.88)",
    padding: 8,
    gap: 6,
    shadowColor: "#000",
    shadowOpacity: 0.04,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 5 },
  },
  songItem: {
    minHeight: 48,
    borderRadius: 13,
    paddingHorizontal: 10,
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
  },
  songItemActive: {
    backgroundColor: "#202020",
  },
  songIndexWrap: {
    width: 26,
    alignItems: "center",
  },
  songIndex: {
    color: "#aaa59b",
    fontSize: 11,
    fontWeight: "900",
  },
  songIndexActive: {
    color: "#f15f5f",
    fontSize: 10,
  },
  songThumb: {
    width: 32,
    height: 32,
    borderRadius: 7,
  },
  songMeta: {
    flex: 1,
  },
  listSongTitle: {
    color: "#252525",
    fontSize: 13,
    lineHeight: 16,
    fontWeight: "900",
  },
  listSongTitleActive: {
    color: "#ffffff",
  },
  listSongArtist: {
    color: "#8a857c",
    fontSize: 11,
    lineHeight: 14,
    marginTop: 2,
    fontWeight: "600",
  },
  listSongArtistActive: {
    color: "#cfcac1",
  },
  songTime: {
    color: "#aaa59b",
    fontSize: 11,
    fontWeight: "900",
  },
  songTimeActive: {
    color: "#ffffff",
  },
  playerBar: {
    width: 770,
    minHeight: 86,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: "#efeee9",
    backgroundColor: "rgba(255,255,255,0.88)",
    paddingHorizontal: 18,
    paddingVertical: 14,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 22,
    shadowColor: "#000",
    shadowOpacity: 0.06,
    shadowRadius: 16,
    shadowOffset: { width: 0, height: 6 },
  },
  trackInfo: {
    width: 172,
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
  },
  albumArt: {
    width: 42,
    height: 42,
    borderRadius: 21,
  },
  songTitle: {
    color: "#202020",
    fontSize: 14,
    lineHeight: 17,
    fontWeight: "900",
  },
  songArtist: {
    color: "#77736b",
    fontSize: 11,
    lineHeight: 14,
    marginTop: 3,
    fontWeight: "600",
  },
  playerCenter: {
    flex: 1,
    alignItems: "center",
    gap: 10,
  },
  playerButtons: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 18,
  },
  iconButton: {
    width: 26,
    height: 26,
    alignItems: "center",
    justifyContent: "center",
  },
  playButton: {
    width: 46,
    height: 46,
    borderRadius: 23,
    backgroundColor: "#202020",
    alignItems: "center",
    justifyContent: "center",
  },
  timelineRow: {
    width: "100%",
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
  },
  timeText: {
    color: "#a4a19a",
    fontSize: 11,
    lineHeight: 12,
    fontWeight: "800",
  },
  timeline: {
    flex: 1,
    height: 4,
    borderRadius: 999,
    backgroundColor: "#dedbd3",
    justifyContent: "center",
  },
  timelineFill: {
    minWidth: 14,
    height: 4,
    borderRadius: 999,
    backgroundColor: "#202020",
    alignItems: "flex-end",
    justifyContent: "center",
  },
  timelineKnob: {
    width: 14,
    height: 14,
    borderRadius: 7,
    backgroundColor: "#202020",
  },
  playerRight: {
    width: 176,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "flex-end",
    gap: 12,
  },
  rpmBadge: {
    height: 30,
    paddingHorizontal: 12,
    borderRadius: 999,
    backgroundColor: "#f5f4f1",
    flexDirection: "row",
    alignItems: "center",
    gap: 7,
  },
  rpmText: {
    color: "#706b62",
    fontSize: 11,
    fontWeight: "900",
  },
  volumeTrack: {
    width: 70,
    height: 4,
    borderRadius: 999,
    backgroundColor: "#dedbd3",
    justifyContent: "center",
  },
  volumeFill: {
    minWidth: 14,
    height: 4,
    borderRadius: 999,
    backgroundColor: "#202020",
    alignItems: "flex-end",
    justifyContent: "center",
  },
  volumeKnob: {
    width: 14,
    height: 14,
    borderRadius: 7,
    backgroundColor: "#202020",
  },
  pressed: {
    opacity: 0.75,
  },
});



