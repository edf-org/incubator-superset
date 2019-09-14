import React from "react";
import PropTypes from "prop-types";
import html2canvas from "html2canvas";

// dataUrl will be used to save in Postgres, and is the default value
const propTypes = {
  returnValue: PropTypes.oneOf(["dataUrl", "href"]),
  width: PropTypes.number,
  height: PropTypes.number,
  lookupClass: PropTypes.string,
  // getElementsByClassName returns an arr under classname,
  lookupIndex: PropTypes.number,
  // getElementById returns Element with ID
  lookupId: PropTypes.string,
  // are we looking up by Id or Class ?
  isId: PropTypes.bool
};

const defaultProps = {
  lookupClass: "chart-container",
  returnValue: "dataUrl",
  isId: false,
  lookupIndex: 0
};

export default async function Screenshot({
  returnValue,
  width,
  height,
  lookupClass,
  lookupIndex,
  isId
} = defaultProps) {
  let capture;
  let imageData;
  isId
    ? (capture = document.getElementById(lookupId))
    : (capture = document.getElementsByClassName(lookupClass)[lookupIndex]);
  if (!!capture) {
    return html2canvas(capture).then(canvas => {
      imageData = canvas.toDataURL("image/png");
      return imageData;
    });
  } else {
      return Promise.resolve()
  }
}
