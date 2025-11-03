import React,{Component} from 'react';
import {Modal} from 'react-bootstrap';
import {Button} from 'react-bootstrap';

class CheckoutModal extends Component{
  state = {
    first_name: "",
    last_name: "",
    phone_number: "",
    address: "",
    waitTillCheckoutEnds: false,
  }

  saveFirstname = event => {
    const {target : {value}}  = event;
    this.setState({
      first_name : value
    });
  }

  saveLastname = event => {
    const {target : {value}}  = event;
    this.setState({
      last_name : value
    });
  }

  savePhonenumber = (event) => {
    const {target : {value}} = event;
    this.setState({
      phone_number : value
    });
  }

  saveAddress = event => {
    const {target : {value}} = event;
    this.setState({
      address : value
    });
  }

  async submit(event){
    event.preventDefault();

    this.setState({
      waitTillCheckoutEnds : true,
    });

    try {
      await this.props.handleCheckout(this.state);

    } finally {
      this.setState({
        waitTillCheckoutEnds : false,
      });
    }
  }

  render(){
    return (
      <Modal show={this.props.checkoutModalActive} onHide={this.props.handleCheckoutModalClose}>
        <form onSubmit={event=>this.submit(event)}>
          <Modal.Header closeButton>
            <h2>
              <center>
                <Modal.Title>Оформление заказа</Modal.Title>
              </center>
            </h2>
          </Modal.Header>
          <Modal.Body>
            <div className="form-group container-fluid">
              <label htmlFor="first_name">Имя:</label>
              <input onChange={this.saveFirstname} required id="first_name" type="text" className="form-control"/><br/>
              <label htmlFor="last_name">Фамилия:</label>
              <input onChange={this.saveLastname} required id="last_name" type="text" className="form-control"/><br/>
              <label htmlFor="phone_number">Телефон:</label>
              <input onChange={this.savePhonenumber} required id="phone_number" maxLength="20" type="tel" className="form-control" placeholder="+7 901 ..."/><br/>
              <label htmlFor="address">Адрес доставки:</label>
              <input onChange={this.saveAddress} required id="address" type="text" maxLength="256" className="form-control" placeholder="Город, улица, дом"/><br/>
            </div>
          </Modal.Body>
          <Modal.Footer>
            <Button id="order-submit-btn" className="btn btn-primary" type="submit" disabled={ this.state.waitTillCheckoutEnds }>
              Отправить
            </Button>
            <Button onClick={this.props.handleCheckoutModalClose}>Закрыть</Button>
          </Modal.Footer>
        </form>
      </Modal>
    );
  }
}

export default CheckoutModal;
