export default function sketch(p){
    let canvasObj;
    
    p.setup = () => {
        canvasObj = p.createCanvas(1160, 700);
    }

    p.draw = () => {}

    p.mouseDragged = () => {
        p.stroke(0);
        p.strokeWeight(2);
        p.line(p.mouseX, p.mouseY, p.pmouseX, p.pmouseY);
    }

    p.myCustomRedrawAccordingToNewPropsHandler = (props) => {
        if(props.evaluate) {
            if(canvasObj) {
                canvasObj.loadPixels();
                let data = canvasObj.canvas.toDataURL();
                props.callBack(data);
            }
        }
        if(props.color){
            p.background(240);
        }
    }
}