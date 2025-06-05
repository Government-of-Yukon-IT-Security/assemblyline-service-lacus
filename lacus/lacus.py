from assemblyline_v4_service.common.base import ServiceBase
from assemblyline_v4_service.common.request import ServiceRequest
from assemblyline_v4_service.common.result import Result, ResultSection, BODY_FORMAT, ResultImageSection, ResultKeyValueSection

import yaml
from pylacus import PyLacus
from pylacus.api import CaptureStatus
from time import sleep
import json

class Lacus(ServiceBase):
    def __init__(self, config=None):
        super(Lacus, self).__init__(config)

    def start(self):
        # ==================================================================
        # Startup actions:
        #   Your service might have to do some warming up on startup to make things faster
        # ==================================================================

        self.log.info(f"start() from {self.service_attributes.name} service called")

        self.lacus = PyLacus("http://127.0.0.1:7100")

    def execute(self, request: ServiceRequest) -> None:
        # ==================================================================
        # Execute a request:
        #   Every time your service receives a new file to scan, the execute function is called.
        #   This is where you should execute your processing code.
        #   For this example, we will only generate results ...
        # ==================================================================

        # Get the request data
        with open(request.file_path, 'r') as f:
            data = yaml.safe_load(f)

        data.pop("uri")

        # Enqueue a request to Lacus
        uuid = self.lacus.enqueue(url=request.task.fileinfo.uri_info.uri, with_favicon=True)

        # Wait for the result
        while self.lacus.get_capture_status(uuid) != CaptureStatus.DONE: # 1 means completed
            sleep(1)

        # Get the result
        data = self.lacus.get_capture(uuid)

        # Create a result object where all the result sections will be saved to
        result = Result()

        url_section = ResultSection('Last Redirected URL', body_format=BODY_FORMAT.URL,
                            body=json.dumps({"name": data['last_redirected_url'], "url": data['last_redirected_url']}))
        url_section.add_tag("network.static.domain", data['last_redirected_url'])

        result.add_section(url_section)

        # Save the HAR file to the result
        with open('capture.har', 'w') as f:
            json.dump(data['har'], f)
        request.add_supplementary(
            'capture.har',
            'capture.har',
            f"HAR file of {data['last_redirected_url']}"
        )

        # Save cookies to the result
        if data.get('cookies'):
            for cookie in data['cookies']:
                cookies_section = ResultKeyValueSection(f'Cookies: {cookie["name"]}')
                for key, value in cookie.items():
                    cookies_section.set_item(key, value)

                result.add_section(cookies_section)

            with open('cookies.json', 'w') as f:
                json.dump(data['cookies'], f)
            request.add_supplementary(
                'cookies.json',
                'cookies.json',
                f"Cookies of {data['last_redirected_url']}"
            )

        # Log any response error codes
        if data.get('error'):
            errors_section = ResultSection('Response Error Codes')
            errors_section.add_line(data['error'])

            result.add_section(errors_section)

        # Save HTML content to the result
        with open('page.html', 'w') as f:
            f.write(data['html'])
        request.add_supplementary(
            'page.html',
            'page.html',
            f"HTML content of {data['last_redirected_url']}"
        )

        # Save screenshot to the result
        with open('screenshot.png', 'wb') as f:
            f.write(data['png'])

        screenshot_section = ResultImageSection(
            request, title_text="Screenshot of visited page", parent=request.result
        )
        screenshot_section.add_image(
            path='screenshot.png',
            name="screenshot.png",
            description=f"Screenshot of {request.task.fileinfo.uri_info.uri}",
        )
        screenshot_section.promote_as_screenshot()

        result.add_section(screenshot_section)

        # Save downloaded files to the result
        if data.get('downloaded_filename'):
            # A file exists
            with open(data['downloaded_filename'], 'wb') as f:
                f.write(data['downloaded_file'])
            request.add_extracted(
                data['downloaded_filename'],
                data['downloaded_filename'],
                f"Auto-Downloaded file from {data['last_redirected_url']}"
            )

        # Save favicons to the result
        if data.get('potential_favicons'):
            # the set of potential favicons
            i = 0
            favicon_section= ResultImageSection(
                request, title_text="Potential Favicons", parent=request.result
            )
            for potential_icon in data['potential_favicons']:
                icon_filename = f"favicon_{i}.ico"
                with open(icon_filename, 'wb') as f:
                    f.write(potential_icon)
                favicon_section.add_image(
                    path=icon_filename,
                    name=icon_filename,
                    description=f"Potential favicon {i} from {data['last_redirected_url']}",
                )
                i += 1
            result.add_section(favicon_section)

        # Save metadata
        meta_section = ResultKeyValueSection('Runtime Metadata')
        meta_section.set_item('Status', data['status'])
        meta_section.set_item('Runtime', data['runtime'])
        meta_section.set_item('Lacus_UUID', uuid)

        result.add_section(meta_section)

        # Save raw json response
        json_data = self.lacus.get_capture(uuid=uuid,  decode=False)
        with open('results.json', 'w') as f:
            json.dump(json_data, f)
        request.add_supplementary(
            'results.json',
            'results.json',
            f"Raw JSON response from Lacus for {data['last_redirected_url']}"
        )

        # Wrap-up: Save your result object back into the request
        request.result = result
