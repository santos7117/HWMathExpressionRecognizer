import React, { Component } from "react";
import P5Wrapper from "react-p5-wrapper";
import { Col, Container, Row } from "react-bootstrap";
import "bootstrap/dist/css/bootstrap.min.css";
import sketch from "./sketches/sketch";
import UploadButton from "./UploadButton";
import Output from "./Output";

let savedImage = "";

class Canvas extends Component {
  constructor() {
    super();
    this.state = {
      color: false,
      evaluate: false,
      equation: "",
      formatted_equation: "",
      result: "",
    };
  }

  pseudo = data => {
    savedImage = data;
  };

  sendImgToServer = image => {
    console.log("req:", image);
    let img = image.replace("data:image/png;base64,", "");

    let data = {};
    data.image = img;

    fetch("http://127.0.0.1:5000/predict", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    })
      .then(response => response.json())
      .then(data => {
        let data1 = JSON.parse(data);
        console.log("Success:", data1);
        this.setState({
          color: false,
          evaluate: false,
          // equation: data1["Entered_equation"],
          formatted_equation: data1["Formatted_equation"],
          result: data1["solution"],
        });
        console.log(this.state);
      })
      .catch(error => {
        console.error("Error:", error);
      });
  };

  onClear = () => {
    this.setState({
      color: true,
      evaluate: false,
      equation: "",
      formatted_equation: "",
      result: "",
    });
  };

  onEval = () => {
    this.setState({
      color: false,
      evaluate: true,
      equation: "",
      formatted_equation: "",
      result: "",
    });
  };

  render() {
    return (
      <Container fluid>
        <Row>
          {/* Whiteboard */}
          <Col className="border border-dark" xl={9}>
            <P5Wrapper
              sketch={sketch}
              color={this.state.color}
              evaluate={this.state.evaluate}
              callBack={this.pseudo}
            ></P5Wrapper>
          </Col>

          {/* Interface */}
          <Col xl={3}>
            <br />
            <button
              type="button"
              onClick={
                this.state.evaluate
                  ? () => this.sendImgToServer(savedImage)
                  : this.onEval
              }
              className="btn btn-primary btn-block "
            >
              {this.state.evaluate ? "Evaluate" : "Save"}
            </button>
            <br />
            <button
              type="button"
              onClick={this.onClear}
              className="btn btn-danger btn-block "
            >
              Clear
            </button>
            <br />
            <UploadButton sendImgToServer={this.sendImgToServer} />
          </Col>
        </Row>
        <Row>
          <Output
            // equation={this.state.equation}
            formatted_equation={this.state.formatted_equation}
            // result={this.state.result}
          />
        </Row>
      </Container>
    );
  }
}

export default Canvas;
