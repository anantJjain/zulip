import * as stream_data from "./stream_data";
import {DEFAULT_COLOR} from "./stream_data";

// In an attempt to decrease mixing, set stream bar
// color look like the stream being used.
// (In particular, if there's a color associated with it,
//  have that color be reflected here too.)
export function decorate(stream_id: number | undefined, $element: JQuery): void {
    const color = stream_id === undefined ? DEFAULT_COLOR : stream_data.get_color(stream_id);
    $element.css("background-color", color);
}
