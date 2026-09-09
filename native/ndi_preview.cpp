#include <cstdio>
#include <cstddef>
#include <Processing.NDI.Lib.h>
#include <jpeglib.h>

#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <string>
#include <thread>
#include <vector>

static bool encode_jpeg(
    const NDIlib_video_frame_v2_t& frame,
    std::vector<unsigned char>& output,
    int quality = 70
) {
    if (!frame.p_data || frame.xres <= 0 || frame.yres <= 0) {
        return false;
    }

    jpeg_compress_struct cinfo;
    jpeg_error_mgr jerr;

    cinfo.err = jpeg_std_error(&jerr);
    jpeg_create_compress(&cinfo);

    unsigned char* jpeg_buffer = nullptr;
    unsigned long jpeg_size = 0;

    jpeg_mem_dest(&cinfo, &jpeg_buffer, &jpeg_size);

    cinfo.image_width = frame.xres;
    cinfo.image_height = frame.yres;
    cinfo.input_components = 3;
    cinfo.in_color_space = JCS_RGB;

    jpeg_set_defaults(&cinfo);
    jpeg_set_quality(&cinfo, quality, TRUE);
    jpeg_start_compress(&cinfo, TRUE);

    std::vector<unsigned char> rgb_row(
        static_cast<size_t>(frame.xres) * 3
    );

    while (cinfo.next_scanline < cinfo.image_height) {

        const uint8_t* source =
            frame.p_data +
            static_cast<size_t>(cinfo.next_scanline) *
            frame.line_stride_in_bytes;

        for (int x = 0; x < frame.xres; ++x) {
            const uint8_t* pixel =
                source + static_cast<size_t>(x) * 4;

            rgb_row[x * 3 + 0] = pixel[2];
            rgb_row[x * 3 + 1] = pixel[1];
            rgb_row[x * 3 + 2] = pixel[0];
        }

        JSAMPROW row = rgb_row.data();
        jpeg_write_scanlines(&cinfo, &row, 1);
    }

    jpeg_finish_compress(&cinfo);

    output.assign(
        jpeg_buffer,
        jpeg_buffer + jpeg_size
    );

    free(jpeg_buffer);
    jpeg_destroy_compress(&cinfo);

    return true;
}

int main(int argc, char* argv[]) {

    if (argc < 2) {
        std::cerr
            << "Usage: ndi_preview \"Exact NDI Source Name\"\n";
        return 1;
    }

    const std::string requested_name = argv[1];

    if (!NDIlib_initialize()) {
        std::cerr << "NDI initialization failed.\n";
        return 1;
    }

    NDIlib_find_create_t find_desc {};
    find_desc.show_local_sources = true;
    find_desc.p_groups = nullptr;
    find_desc.p_extra_ips = nullptr;

    NDIlib_find_instance_t finder =
        NDIlib_find_create_v2(&find_desc);

    if (!finder) {
        std::cerr << "Unable to create NDI finder.\n";
        NDIlib_destroy();
        return 2;
    }

    std::cerr
        << "Searching for exact source: "
        << requested_name
        << "\n";

    const NDIlib_source_t* selected = nullptr;

    auto deadline =
        std::chrono::steady_clock::now() +
        std::chrono::seconds(20);

    while (std::chrono::steady_clock::now() < deadline) {

        NDIlib_find_wait_for_sources(finder, 1000);

        uint32_t count = 0;

        const NDIlib_source_t* sources =
            NDIlib_find_get_current_sources(
                finder,
                &count
            );

        std::cerr
            << "Finder sees "
            << count
            << " source(s)\n";

        for (uint32_t i = 0; i < count; ++i) {

            const char* name =
                sources[i].p_ndi_name
                ? sources[i].p_ndi_name
                : "";

            const char* url =
                sources[i].p_url_address
                ? sources[i].p_url_address
                : "";

            std::cerr
                << "  [" << i << "] "
                << name
                << " -> "
                << url
                << "\n";

            if (requested_name == name) {
                selected = &sources[i];
                break;
            }
        }

        if (selected) {
            break;
        }
    }

    if (!selected) {
        std::cerr << "Exact source was not found.\n";

        NDIlib_find_destroy(finder);
        NDIlib_destroy();
        return 3;
    }

    std::cerr
        << "Matched source: "
        << selected->p_ndi_name
        << "\n";

    /*
     * Important:
     * Create/connect the receiver while the finder is still alive.
     * The source structure returned by the finder belongs to the SDK.
     */

    NDIlib_recv_create_v3_t recv_desc {};

    recv_desc.source_to_connect_to = *selected;

    recv_desc.color_format =
        NDIlib_recv_color_format_BGRX_BGRA;

    recv_desc.bandwidth =
        NDIlib_recv_bandwidth_highest;

    recv_desc.allow_video_fields = false;

    recv_desc.p_ndi_recv_name =
        "Fordo NDI Preview";

    NDIlib_recv_instance_t receiver =
        NDIlib_recv_create_v3(&recv_desc);

    if (!receiver) {
        std::cerr << "Unable to create NDI receiver.\n";

        NDIlib_find_destroy(finder);
        NDIlib_destroy();
        return 4;
    }

    std::cerr << "Receiver created. Waiting for media...\n";

    std::vector<unsigned char> jpeg;

    while (true) {

        NDIlib_video_frame_v2_t video {};
        NDIlib_audio_frame_v2_t audio {};
        NDIlib_metadata_frame_t metadata {};

        const NDIlib_frame_type_e type =
            NDIlib_recv_capture_v2(
                receiver,
                &video,
                &audio,
                &metadata,
                2000
            );

        if (type == NDIlib_frame_type_video) {

            std::cerr
                << "VIDEO "
                << video.xres
                << "x"
                << video.yres
                << " stride="
                << video.line_stride_in_bytes
                << "\n";

            if (encode_jpeg(video, jpeg)) {

                std::cout
                    << "--frame\r\n"
                    << "Content-Type: image/jpeg\r\n"
                    << "Content-Length: "
                    << jpeg.size()
                    << "\r\n\r\n";

                std::cout.write(
                    reinterpret_cast<const char*>(
                        jpeg.data()
                    ),
                    jpeg.size()
                );

                std::cout << "\r\n";
                std::cout.flush();
            }

            NDIlib_recv_free_video_v2(
                receiver,
                &video
            );
        }
        else if (type == NDIlib_frame_type_audio) {

            std::cerr << "AUDIO\n";

            NDIlib_recv_free_audio_v2(
                receiver,
                &audio
            );
        }
        else if (type == NDIlib_frame_type_metadata) {

            std::cerr << "METADATA\n";

            NDIlib_recv_free_metadata(
                receiver,
                &metadata
            );
        }
        else if (type == NDIlib_frame_type_status_change) {

            std::cerr << "STATUS CHANGE\n";
        }
        else if (type == NDIlib_frame_type_error) {

            std::cerr << "RECEIVER ERROR\n";
        }
        else {

            std::cerr << "No frame / timeout\n";
        }
    }

    NDIlib_recv_destroy(receiver);
    NDIlib_find_destroy(finder);
    NDIlib_destroy();

    return 0;
}
